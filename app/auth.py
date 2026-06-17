import uuid

from fastapi import Depends, HTTPException, status
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport, JWTStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_async_session
from app.models import ROLE_ADMIN, User


settings = get_settings()

TOKEN_LIFETIME_SECONDS = 60 * 60 * 24 * 7


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.jwt_secret
    verification_token_secret = settings.jwt_secret

    async def create(self, user_create, safe: bool = False, request=None):
        email_domain = user_create.email.split("@")[-1].lower()
        if email_domain != settings.allowed_email_domain.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration is restricted to @{settings.allowed_email_domain} email addresses.",
            )
        return await super().create(user_create, safe=safe, request=request)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = CookieTransport(
    cookie_max_age=TOKEN_LIFETIME_SECONDS,
    cookie_secure=settings.cookie_secure,
    cookie_httponly=True,
    cookie_samesite="lax",
)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=settings.jwt_secret, lifetime_seconds=TOKEN_LIFETIME_SECONDS)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)


def require_roles(*allowed_roles: str):
    async def role_checker(user: User = Depends(current_active_user)) -> User:
        if user.role == ROLE_ADMIN:
            return user
        if user.role in allowed_roles:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted.")

    return role_checker


current_trainer = require_roles("trainer")
current_admin = require_roles("admin")
