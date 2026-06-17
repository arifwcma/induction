from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


ROLE_BASIC = "basic"
ROLE_TRAINER = "trainer"
ROLE_ADMIN = "admin"


class User(SQLAlchemyBaseUserTableUUID, Base):
    full_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    role: Mapped[str] = mapped_column(String(20), default=ROLE_BASIC, nullable=False)
