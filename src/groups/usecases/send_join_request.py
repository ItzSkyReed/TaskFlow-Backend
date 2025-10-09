from uuid import UUID

from sqlalchemy import func, literal, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User
from ...utils import lock_rows
from .. import JoinRequestStatus
from ..exceptions import (
    GroupIsFullException,
    GroupNotFoundException,
    UserAlreadyInGroupRequestException,
)
from ..models import Group, GroupJoinRequest, GroupMember
from ..schemas import JoinRequestSchema


async def send_join_request(
    group_id: UUID,
    requester_id: UUID,
    session: AsyncSession,
) -> JoinRequestSchema:
    """
    Отправка запроса на вступление в группу
    :param requester_id: ID пользователя отправляющего заявку в группу
    :param group_id: ID группы, в которую пользователь отправляет заявку
    :param session: Сессия
    """

    # Блокируем группу
    group = (await lock_rows(session, Group, Group.id == group_id)).scalar_one_or_none()
    if not group:
        raise GroupNotFoundException()

    # Блокируем всех участников группы
    await lock_rows(session, GroupMember, GroupMember.group_id == group_id)

    if (
        await session.execute(
            select(GroupMember)
            .where(
                or_(
                    # пользователь уже в участниках
                    (GroupMember.user_id == requester_id) & (GroupMember.group_id == group_id),
                    # пользователь — создатель группы
                    (Group.creator_id == requester_id) & (Group.id == group_id),
                )
            )
            .join(Group, Group.id == GroupMember.group_id, isouter=True)
        )
    ).scalar_one_or_none():
        raise UserAlreadyInGroupRequestException()

    # Считаем количество участников
    members_count = (
        await session.execute(select(func.count(GroupMember.user_id)).where(GroupMember.group_id == group_id))
    ).scalar_one()

    if members_count >= group.max_members:
        raise GroupIsFullException()

    await session.execute(
        insert(GroupJoinRequest)
        .values(group_id=group_id, requester_id=requester_id)
        .on_conflict_do_nothing(
            index_elements=["group_id", "requester_id"],
            index_where=(GroupJoinRequest.status == literal(JoinRequestStatus.PENDING, literal_execute=True)),
        )
    )

    join_request = (
        await session.execute(
            select(GroupJoinRequest)
            .where(
                GroupJoinRequest.group_id == group_id,
                GroupJoinRequest.requester_id == requester_id,
                GroupJoinRequest.status == JoinRequestStatus.PENDING,
            )
            .options(
                joinedload(GroupJoinRequest.group).selectinload(Group.members),
                joinedload(GroupJoinRequest.requester).joinedload(User.user_profile),
            )
            .with_for_update(of=GroupJoinRequest)
        )
    ).scalar_one_or_none()

    if not join_request:  # pragma: no cover
        raise GroupIsFullException()

    join_request_schema = await ObjectMapper.map(
        join_request, JoinRequestSchema, user_id=requester_id, session=session
    )
    await session.commit()
    return join_request_schema
