import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ROLE_ADMIN, User


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
