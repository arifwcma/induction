from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from llama_index.core.llms import ChatMessage, MessageRole
from pydantic import BaseModel
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from app.auth import auth_backend, current_active_user, current_admin, current_trainer, fastapi_users
from app.kb_store import create_kb_entry
from app.models import KB_KIND_DOCUMENT, KB_KIND_MESSAGE
from app.trainer_kb import add_text_to_knowledge_base, extract_text_from_upload
from app.chat_store import (
    build_cross_session_context,
    get_or_create_session,
    get_owned_session,
    list_user_sessions,
    load_history,
    persist_turn,
    session_message_payload,
    set_session_summary,
)
from app.config import get_settings
from app.config_store import ensure_prompt_seeded, get_system_prompt, update_system_prompt
from app.db import async_session_maker, create_db_and_tables
from app.models import User
from app.rag.chat import DEFAULT_SYSTEM_PROMPT, answer_stream, summarise_conversation
from app.schemas import UserCreate, UserRead, UserUpdate


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    async with async_session_maker() as db:
        await ensure_prompt_seeded(db, DEFAULT_SYSTEM_PROMPT)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.post("/chat")
async def chat(request: ChatRequest, user: User = Depends(current_active_user)):
    async def stream_and_persist():
        async with async_session_maker() as db:
            chat_session = await get_or_create_session(
                db, user.id, request.session_id, request.message
            )
            history = await load_history(db, chat_session.id)
            cross_session_context = await build_cross_session_context(
                db, user.id, chat_session.id
            )
            system_prompt = await get_system_prompt(db, DEFAULT_SYSTEM_PROMPT)

            answer_pieces = []
            stream = answer_stream(
                system_prompt, history, cross_session_context, request.message
            )
            async for delta in iterate_in_threadpool(stream):
                answer_pieces.append(delta)
                yield delta

            answer_text = "".join(answer_pieces)
            await persist_turn(db, chat_session.id, request.message, answer_text)

            updated_history = history + [
                ChatMessage(role=MessageRole.USER, content=request.message),
                ChatMessage(role=MessageRole.ASSISTANT, content=answer_text),
            ]
            new_summary = await run_in_threadpool(summarise_conversation, updated_history)
            await set_session_summary(db, chat_session.id, new_summary)

    return StreamingResponse(stream_and_persist(), media_type="text/plain")


@app.get("/sessions")
async def get_sessions(user: User = Depends(current_active_user)):
    async with async_session_maker() as db:
        sessions = await list_user_sessions(db, user.id)
        return [
            {
                "session_id": session.client_key,
                "title": session.title,
                "updated_at": session.updated_at,
            }
            for session in sessions
        ]


@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, user: User = Depends(current_active_user)):
    async with async_session_maker() as db:
        chat_session = await get_owned_session(db, user.id, session_id)
        if chat_session is None:
            raise HTTPException(status_code=404, detail="Session not found.")
        return await session_message_payload(db, chat_session.id)


class PromptUpdate(BaseModel):
    prompt: str


@app.get("/admin/prompt")
async def read_prompt(admin: User = Depends(current_admin)):
    async with async_session_maker() as db:
        return {"prompt": await get_system_prompt(db, DEFAULT_SYSTEM_PROMPT)}


@app.put("/admin/prompt")
async def write_prompt(update: PromptUpdate, admin: User = Depends(current_admin)):
    async with async_session_maker() as db:
        await update_system_prompt(db, update.prompt)
        return {"prompt": await get_system_prompt(db, DEFAULT_SYSTEM_PROMPT)}


def trainer_display_name(trainer: User) -> str:
    return trainer.full_name.strip() or trainer.email


class KBTextRequest(BaseModel):
    content: str


@app.post("/kb/text")
async def add_message_to_kb(request: KBTextRequest, trainer: User = Depends(current_trainer)):
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Cannot add empty text to the knowledge base.")

    trainer_name = trainer_display_name(trainer)
    source_label = f"Trainer note by {trainer_name}"

    async with async_session_maker() as db:
        entry = await create_kb_entry(
            db, trainer.id, trainer_name, KB_KIND_MESSAGE, source_label, content
        )

    await run_in_threadpool(
        add_text_to_knowledge_base, content, source_label, trainer_name, str(entry.id)
    )
    return {"id": str(entry.id), "source_label": source_label}


@app.post("/kb/document")
async def add_document_to_kb(
    file: UploadFile = File(...), trainer: User = Depends(current_trainer)
):
    raw_bytes = await file.read()
    try:
        extracted_text = await run_in_threadpool(
            extract_text_from_upload, file.filename, raw_bytes
        )
    except ValueError as unsupported_file:
        raise HTTPException(status_code=400, detail=str(unsupported_file))

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in the uploaded file.")

    trainer_name = trainer_display_name(trainer)
    source_label = file.filename

    async with async_session_maker() as db:
        entry = await create_kb_entry(
            db,
            trainer.id,
            trainer_name,
            KB_KIND_DOCUMENT,
            source_label,
            extracted_text,
            filename=file.filename,
        )

    await run_in_threadpool(
        add_text_to_knowledge_base, extracted_text, source_label, trainer_name, str(entry.id)
    )
    return {"id": str(entry.id), "filename": file.filename}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
