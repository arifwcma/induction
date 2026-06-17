import asyncio

from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from app.auth import UserManager
from app.config import get_settings
from app.db import async_session_maker, create_db_and_tables
from app.models import ROLE_ADMIN, User
from app.schemas import UserCreate


async def seed_admin():
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        print("ADMIN_EMAIL / ADMIN_PASSWORD not set; skipping admin seed.")
        return

    await create_db_and_tables()

    async with async_session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User)
        manager = UserManager(user_db)

        admin_account = UserCreate(
            email=settings.admin_email,
            password=settings.admin_password,
            full_name="Administrator",
        )

        try:
            user = await manager.create(admin_account, safe=False)
            print(f"Created admin account {user.email}.")
        except UserAlreadyExists:
            user = await user_db.get_by_email(settings.admin_email)
            print(f"Admin account {settings.admin_email} already exists; ensuring admin role.")

        user.role = ROLE_ADMIN
        user.is_superuser = True
        session.add(user)
        await session.commit()
        print("Admin role ensured.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
