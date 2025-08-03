from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy import Enum as PgEnum
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import text

from ..database import Base

if TYPE_CHECKING:
    from ..user import User


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    name: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    description: Mapped[str] = mapped_column(String(5000), nullable=True)

    creator_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    creator: Mapped["User"] = relationship(back_populates="created_groups")

    members: Mapped[list["GroupMembers"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    invitations: Mapped[list["GroupInvitation"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class GroupMembers(Base):
    __tablename__ = "group_members"

    id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    group_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        unique=False,
        nullable=False,
    )  # Группа в которой состоит пользователь

    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=False,
        nullable=False,
    )  # Пользователь

    joined_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )  # Время входа пользователя в группу

    # ORM-связи
    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="group_memberships")

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_members_group_user"),
    )


class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class GroupInvitation(Base):
    __tablename__ = "group_invitations"

    id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    group_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        unique=False,
        nullable=False,
    )  # Группа куда приглашается юзер

    inviter_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=False,
        nullable=False,
    )  # Приглашающий юзер

    invitee_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=False,
        nullable=False,
    )  # Приглашенный юзер

    status: Mapped[InvitationStatus] = mapped_column(
        PgEnum(InvitationStatus, name="status"),
        server_default=text(f"'{InvitationStatus.PENDING.name}'::status"),
        nullable=False,
    )  # Статус заявки

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )  # Время отправки приглашения

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=datetime.now
    )  # Время изменения статуса приглашения (pending -> approved)

    group: Mapped["Group"] = relationship(back_populates="invitations")
    inviter: Mapped["User"] = relationship(foreign_keys=[inviter_id])
    invitee: Mapped["User"] = relationship(foreign_keys=[invitee_id])

    __table_args__ = (
        # Данный индекс позволяет иметь сколько угодно отклоненных и принятых приглашений, но только 1 ожидающее на уровне БД
        Index(
            "uq_group_invitation_pending",
            "group_id",
            "invitee_id",  # поля, к которым применим
            unique=True,
            postgresql_where=text(
                f"status = '{InvitationStatus.PENDING.name}'::status"
            ),
        ),
    )
