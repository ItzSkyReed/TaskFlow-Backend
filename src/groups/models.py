from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as PgEnum
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import text

from ..database import Base

if TYPE_CHECKING:
    from ..user import User


class Group(Base):
    """
    Хранение групп
    """

    __tablename__ = "groups"

    id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    name: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # Название группы

    has_avatar: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    creator_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        # Не позволяем удалить пользователя пока у него есть владельцы, сначала их надо передать кому-либо
        # (возможно автоматически тем, у кого самые большие права,
        # возможно случайному, возможно ему самому надо будет выбрать будущего владельца)
        nullable=False,
        index=True,
    )  # UUID пользователя создавшего группу (владелец)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )  # Время создания группы

    creator: Mapped[User] = relationship(back_populates="created_groups")

    members: Mapped[list["GroupMembers"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    invitations: Mapped[list["GroupInvitation"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )


class GroupMembers(Base):
    """
    Хранение участников групп
    """

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

    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="group_memberships")

    permission_objs: Mapped[list["GroupUserPermission"]] = relationship(
        "GroupUserPermission",
        primaryjoin="and_(GroupMembers.user_id == foreign(GroupUserPermission.user_id),"
        "GroupMembers.group_id == foreign(GroupUserPermission.group_id))",
        viewonly=True,
        lazy="selectin",
    )

    @property
    def permissions(self) -> list[str]:
        """Список строк прав"""
        return [perm.permission.value for perm in self.permission_objs]

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_members_group_user"),
    )


class InvitationStatus(str, Enum):
    """
    Статусы заявок приглашений
    """

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class GroupInvitation(Base):
    """
    Хранение приглашений пользователей в группы
    """

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
    inviter: Mapped[User] = relationship(foreign_keys=[inviter_id])
    invitee: Mapped[User] = relationship(foreign_keys=[invitee_id])

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


# Идея с запросами в группу

# class JoinRequestStatus(str, Enum):
#     PENDING = "PENDING"
#     APPROVED = "APPROVED"
#     REJECTED = "REJECTED"
#
# class GroupJoinRequest(Base):
#     __tablename__ = "group_join_requests"
#
#     id: Mapped[UUID] = mapped_column(
#         pgUUID(as_uuid=True),
#         primary_key=True,
#         server_default=text("uuid_generate_v4()"),
#     )
#
#     group_id: Mapped[UUID] = mapped_column(
#         pgUUID(as_uuid=True),
#         ForeignKey("groups.id", ondelete="CASCADE"),
#         nullable=False,
#     )  # Группа, куда хочет вступить пользователь
#
#     requester_id: Mapped[UUID] = mapped_column(
#         pgUUID(as_uuid=True),
#         ForeignKey("users.id", ondelete="CASCADE"),
#         nullable=False,
#     )  # Пользователь, подавший заявку
#
#     status: Mapped[JoinRequestStatus] = mapped_column(
#         PgEnum(JoinRequestStatus, name="join_request_status"),
#         server_default=text(f"'{JoinRequestStatus.PENDING.name}'::join_request_status"),
#         nullable=False,
#     )
#
#     created_at: Mapped[datetime] = mapped_column(
#         DateTime, server_default=func.now(), nullable=False
#     )
#
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime, nullable=False, server_default=func.now(), onupdate=datetime.now
#     )
#
#     group: Mapped["Group"] = relationship()
#     requester: Mapped["User"] = relationship()
#
#     __table_args__ = (
#         Index(
#             "uq_group_join_request_pending",
#             "group_id",
#             "requester_id",
#             unique=True,
#             postgresql_where=text(
#                 f"status = '{JoinRequestStatus.PENDING.name}'::join_request_status"
#             ),
#         ),
#     )
