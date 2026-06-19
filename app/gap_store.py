import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KnowledgeGap, User


async def log_gap(
    db: AsyncSession,
    user_id: uuid.UUID,
    session_key: str,
    question: str,
    topic: str,
):
    gap = KnowledgeGap(
        user_id=user_id,
        session_key=session_key,
        question=question,
        topic=topic,
    )
    db.add(gap)
    await db.commit()


async def list_gaps(db: AsyncSession) -> list[tuple[KnowledgeGap, str]]:
    query = (
        select(KnowledgeGap, User.email)
        .join(User, KnowledgeGap.user_id == User.id, isouter=True)
        .order_by(KnowledgeGap.created_at.desc())
    )
    rows = (await db.execute(query)).all()
    return [(gap, email or "") for gap, email in rows]


async def get_gap(db: AsyncSession, gap_id: uuid.UUID) -> KnowledgeGap | None:
    return await db.get(KnowledgeGap, gap_id)


async def set_gap_status(db: AsyncSession, gap: KnowledgeGap, status: str):
    gap.status = status
    await db.commit()


async def delete_user_gaps(db: AsyncSession, user_id: uuid.UUID):
    await db.execute(delete(KnowledgeGap).where(KnowledgeGap.user_id == user_id))
