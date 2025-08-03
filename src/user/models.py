from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BIGINT, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import text

from ..database import Base

if TYPE_CHECKING:
    from ..groups import Group, GroupMembers


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    login: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(319),  # RFC-validated max length
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(128),  # достаточная длина для bcrypt/scrypt/argon2
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )  # Время регистрации

    created_groups: Mapped[list["Group"]] = relationship(
        back_populates="creator", cascade="all, delete-orphan"
    )

    user_profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", uselist=False,
        cascade="all, delete-orphan", passive_deletes=True,
    )

    group_memberships: Mapped[list["GroupMembers"]] = relationship(
        back_populates="user"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey(User.id, ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(32), unique=False, index=True, nullable=False
    )

    discord_id: Mapped[int] = mapped_column(
        BIGINT,
        unique=True,
        nullable=True,
    )

    discord_username: Mapped[str] = mapped_column(
        String(32),  # Макс. длина дискорд юзернейма
        unique=False,
        nullable=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BIGINT,
        unique=True,
        nullable=True,
    )
    telegram_username: Mapped[str] = mapped_column(
        String(32),
        unique=False,
        nullable=True,  # Макс. длина ТГ юзернейма
    )

    # Проверка, что или оба параметра связанные с ТГ пустые, или оба имеют значение
    __table_args__ = (
        CheckConstraint(
            """
            (telegram_id IS NULL AND telegram_username IS NULL)
            OR
            (telegram_id IS NOT NULL AND telegram_username IS NOT NULL)
            """,
            name="ck_telegram_fields_null_together",
        ),
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="user_profile", uselist=False
    )
