import uuid

from llama_index.core.llms import ChatMessage, MessageRole
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChatMessageRecord, ChatSession, KnowledgeGap


MAX_PROFILE_SESSIONS = 10
TITLE_MAX_LENGTH = 60

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"


def title_from_message(message: str) -> str:
    trimmed = message.strip().replace("\n", " ")
    if len(trimmed) <= TITLE_MAX_LENGTH:
        return trimmed or "New chat"
    return trimmed[:TITLE_MAX_LENGTH] + "..."


async def get_or_create_session(
    db: AsyncSession, user_id: uuid.UUID, client_key: str, first_message: str
) -> ChatSession:
    query = select(ChatSession).where(
        ChatSession.user_id == user_id,
        ChatSession.client_key == client_key,
    )
    existing_session = (await db.execute(query)).scalar_one_or_none()
    if existing_session is not None:
        return existing_session

    new_session = ChatSession(
        user_id=user_id,
        client_key=client_key,
        title=title_from_message(first_message),
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


async def load_history(db: AsyncSession, session_id: uuid.UUID) -> list[ChatMessage]:
    query = (
        select(ChatMessageRecord)
        .where(ChatMessageRecord.session_id == session_id)
        .order_by(ChatMessageRecord.created_at)
    )
    records = (await db.execute(query)).scalars().all()

    history = []
    for record in records:
        role = MessageRole.USER if record.role == ROLE_USER else MessageRole.ASSISTANT
        history.append(ChatMessage(role=role, content=record.content))
    return history


async def build_cross_session_context(
    db: AsyncSession, user_id: uuid.UUID, current_session_id: uuid.UUID
) -> str:
    query = (
        select(ChatSession)
        .where(
            ChatSession.user_id == user_id,
            ChatSession.id != current_session_id,
            ChatSession.summary != "",
        )
        .order_by(ChatSession.updated_at.desc())
        .limit(MAX_PROFILE_SESSIONS)
    )
    earlier_sessions = (await db.execute(query)).scalars().all()

    summaries = [session.summary.strip() for session in earlier_sessions if session.summary.strip()]
    return "\n".join(f"- {summary}" for summary in summaries)


async def persist_turn(
    db: AsyncSession, session_id: uuid.UUID, user_text: str, assistant_text: str
):
    db.add(ChatMessageRecord(session_id=session_id, role=ROLE_USER, content=user_text))
    db.add(ChatMessageRecord(session_id=session_id, role=ROLE_ASSISTANT, content=assistant_text))
    await db.commit()


async def set_session_summary(db: AsyncSession, session_id: uuid.UUID, summary: str):
    chat_session = await db.get(ChatSession, session_id)
    if chat_session is not None:
        chat_session.summary = summary
        await db.commit()


async def list_user_sessions(db: AsyncSession, user_id: uuid.UUID) -> list[ChatSession]:
    query = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list((await db.execute(query)).scalars().all())


async def get_owned_session(
    db: AsyncSession, user_id: uuid.UUID, client_key: str
) -> ChatSession | None:
    query = select(ChatSession).where(
        ChatSession.user_id == user_id,
        ChatSession.client_key == client_key,
    )
    return (await db.execute(query)).scalar_one_or_none()


async def delete_owned_session(
    db: AsyncSession, user_id: uuid.UUID, client_key: str
) -> bool:
    """Delete a session (and its messages) if it belongs to the user.

    Returns True if a session was found and deleted, False otherwise. There is no
    DB-level cascade, so the message rows are removed explicitly first. Knowledge
    gaps logged from this conversation are removed too, so they do not outlive the
    chat they came from (the gap's session_key is the session's client_key)."""
    chat_session = await get_owned_session(db, user_id, client_key)
    if chat_session is None:
        return False
    await db.execute(
        delete(ChatMessageRecord).where(ChatMessageRecord.session_id == chat_session.id)
    )
    await db.execute(
        delete(KnowledgeGap).where(
            KnowledgeGap.user_id == user_id,
            KnowledgeGap.session_key == client_key,
        )
    )
    await db.delete(chat_session)
    await db.commit()
    return True


async def session_message_payload(db: AsyncSession, session_id: uuid.UUID) -> list[dict]:
    query = (
        select(ChatMessageRecord)
        .where(ChatMessageRecord.session_id == session_id)
        .order_by(ChatMessageRecord.created_at)
    )
    records = (await db.execute(query)).scalars().all()
    return [{"role": record.role, "content": record.content} for record in records]
