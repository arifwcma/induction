import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ROLE_ADMIN,
    ChatMessageRecord,
    ChatSession,
    KnowledgeGap,
    TrainerKBEntry,
    User,
)


async def list_users(db: AsyncSession) -> list[User]:
    query = select(User).order_by(User.email)
    return list((await db.execute(query)).scalars().all())


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def set_user_role(db: AsyncSession, user: User, role: str):
    user.role = role
    user.is_superuser = role == ROLE_ADMIN
    await db.commit()


async def set_user_password(db: AsyncSession, user: User, hashed_password: str):
    user.hashed_password = hashed_password
    await db.commit()


async def count_admins(db: AsyncSession) -> int:
    query = select(func.count()).select_from(User).where(User.role == ROLE_ADMIN)
    return (await db.execute(query)).scalar_one()


async def delete_user_and_data(db: AsyncSession, user: User):
    """Remove a user and everything that belongs only to them: their chat
    sessions and messages, and their logged knowledge gaps. Knowledge a trainer
    contributed is kept (we just detach it by nulling the trainer link) so the
    bot does not lose what was taught when a trainer leaves."""
    session_ids = (
        (await db.execute(select(ChatSession.id).where(ChatSession.user_id == user.id)))
        .scalars()
        .all()
    )
    if session_ids:
        await db.execute(
            delete(ChatMessageRecord).where(ChatMessageRecord.session_id.in_(session_ids))
        )
    await db.execute(delete(ChatSession).where(ChatSession.user_id == user.id))
    await db.execute(delete(KnowledgeGap).where(KnowledgeGap.user_id == user.id))
    await db.execute(
        update(TrainerKBEntry).where(TrainerKBEntry.trainer_id == user.id).values(trainer_id=None)
    )
    await db.delete(user)
    await db.commit()
