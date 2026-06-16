from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import get_settings
from app.rag.chat import build_chat_engine
from app.sessions import get_memory


settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
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
def chat(request: ChatRequest):
    memory = get_memory(request.session_id)
    chat_engine = build_chat_engine(memory)
    streaming_response = chat_engine.stream_chat(request.message)

    def token_stream():
        for token in streaming_response.response_gen:
            yield token

    return StreamingResponse(token_stream(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
