import uuid
from datetime import datetime

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


ROLE_BASIC = "basic"
ROLE_TRAINER = "trainer"
ROLE_ADMIN = "admin"


class User(SQLAlchemyBaseUserTableUUID, Base):
    full_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=ROLE_BASIC, nullable=False)
    profile_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)


class ChatSession(Base):
    __tablename__ = "chat_session"
    __table_args__ = (UniqueConstraint("user_id", "client_key", name="uq_user_client_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("user.id"), nullable=False, index=True)
    client_key: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="New chat", nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ChatMessageRecord(Base):
    __tablename__ = "chat_message"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chat_session.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SystemPromptConfig(Base):
    __tablename__ = "system_prompt_config"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Clause(Base):
    __tablename__ = "clause"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    clause_number: Mapped[str] = mapped_column(String(40), default="", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    breadcrumb: Mapped[str] = mapped_column(Text, default="", nullable=False)
    scope: Mapped[str] = mapped_column(String(20), default="general", nullable=False)
    condition: Mapped[str] = mapped_column(Text, default="", nullable=False)
    page: Mapped[int] = mapped_column(default=0, nullable=False)
    full_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cross_refs: Mapped[str] = mapped_column(Text, default="", nullable=False)


KB_KIND_MESSAGE = "message"
KB_KIND_DOCUMENT = "document"


class TrainerKBEntry(Base):
    __tablename__ = "trainer_kb_entry"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    trainer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("user.id"), nullable=True, index=True
    )
    trainer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    source_label: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


GAP_STATUS_OPEN = "open"
GAP_STATUS_REVIEWED = "reviewed"
GAP_STATUS_DISMISSED = "dismissed"
GAP_STATUSES = {GAP_STATUS_OPEN, GAP_STATUS_REVIEWED, GAP_STATUS_DISMISSED}


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gap"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("user.id"), nullable=True, index=True
    )
    session_key: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=GAP_STATUS_OPEN, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
