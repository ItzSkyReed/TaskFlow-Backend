from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    SMALLINT,
    Boolean,
    CheckConstraint,
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
from .enums import GroupPermission, InvitationStatus, JoinRequestStatus

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
        String(50), nullable=False, unique=True, index=True
    )  # Название группы

    description: Mapped[str] = mapped_column(
        String(2000), nullable=True
    )  # Описание группы

    max_members: Mapped[int] = mapped_column(
        SMALLINT(), nullable=False, server_default=text("100")
    )  # максимальное кол-во пользователей в группе, если не указано, то 100

    has_avatar: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )  # флаг указывающий наличие аватара у группы, путь к аватару генерируется внутри схемы

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

    creator: Mapped["User"] = relationship(
        back_populates="created_groups"
    )  # Создатель группы

    members: Mapped[list["GroupMember"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )  # Участники группы

    invitations: Mapped[list["GroupInvitation"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )  # Приглашения в группу

    __table_args__ = (
        Index(
            "ix_groups_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),  # Индекс для быстрого поиска по названию группы
        CheckConstraint(
            "max_members BETWEEN 2 AND 100", name="ck_group_max_members"
        ),  # Ограничивает кол-во участников группы от 2 до 100 чел.
    )


class GroupMember(Base):
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

    group: Mapped["Group"] = relationship(
        back_populates="members"
    )  # Группа, участником которой является пользователь
    user: Mapped["User"] = relationship(
        back_populates="group_memberships"
    )  # Пользователь

    permission_objs: Mapped[list["GroupUserPermission"]] = relationship(
        "GroupUserPermission",
        primaryjoin="and_(GroupMember.user_id == foreign(GroupUserPermission.user_id),"
        "GroupMember.group_id == foreign(GroupUserPermission.group_id))",
        viewonly=True,
        lazy="selectin",
    )  # Список прав пользователя в данной группе как колонок таблиц

    @property
    def permissions(self) -> list[GroupPermission]:
        """Список строк прав"""
        return [
            perm.permission for perm in self.permission_objs
        ]  # Список прав пользователя в данной группе как enum-ов прав

    __table_args__ = (
        UniqueConstraint(
            "group_id", "user_id", name="uq_group_members_group_user"
        ),  # Гарантирует что пользователь не добавлен в группу дважды
    )


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
        DateTime, nullable=False, server_default=func.now(), server_onupdate=func.now()
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


class GroupJoinRequest(Base):
    __tablename__ = "group_join_requests"

    id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    group_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )  # Группа, куда хочет вступить пользователь

    requester_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )  # Пользователь, подавший заявку

    status: Mapped[JoinRequestStatus] = mapped_column(
        PgEnum(JoinRequestStatus, name="join_request_status"),
        server_default=text(f"'{JoinRequestStatus.PENDING.name}'::join_request_status"),
        nullable=False,
    )  # Статус заявки на присоединение в группу

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )  # Время создания заявки

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=datetime.now
    )  # Время обновления заявки

    group: Mapped["Group"] = relationship()  # Группа в которую отправлена заявка
    requester: Mapped["User"] = (
        relationship()
    )  # Пользователь отправивший заявку в группу

    __table_args__ = (
        # Гарантирует, что пользователь не сможет второй раз отправить заявку со статусом PENDING, пока 1 есть
        Index(
            "uq_group_join_request_pending",
            "group_id",
            "requester_id",
            unique=True,
            postgresql_where=text(
                f"status = '{JoinRequestStatus.PENDING.name}'::join_request_status"
            ),
        ),
    )


class GroupUserPermission(Base):
    """
    Содержит записи о правах пользователей
    """

    __tablename__ = "group_user_permissions"

    id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )

    group_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # ID группы

    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )  # ID пользователя

    permission: Mapped[GroupPermission] = mapped_column(
        PgEnum(GroupPermission, name="group_permission"), nullable=False
    )  # Право

    granted_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )  # Время выдачи права
    granted_by: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )  # Кем право выдано

    __table_args__ = (
        # Гарантирует, что нет дублированных прав.
        UniqueConstraint(
            "group_id", "user_id", "permission", name="uq_group_user_permission"
        ),
    )
