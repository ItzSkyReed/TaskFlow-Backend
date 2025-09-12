from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User, UserProfile
from .. import GroupMember, GroupPermission, JoinRequestStatus
from ..exceptions import (
    GroupIsFullException,
    GroupJoinRequestAlreadyResolvedException,
    GroupJoinRequestNotFoundException,
    NotEnoughGroupPermissionsException,
)
from ..models import Group, GroupJoinRequest, GroupUserPermission
from ..schemas import (
    JoinRequestSchema,
)


async def respond_to_join_request(
    respond_status: JoinRequestStatus,
    join_request_id: UUID,
    acceptor_id: UUID,
    session: AsyncSession,
) -> JoinRequestSchema:
    """
    Ответ на запрос на вступление в группу
    :param respond_status: Статус ответа на заявку: Принятие/отказ
    :param join_request_id: UUID заявки на вступление
    :param acceptor_id: UUID пользователя, отвечающего на заявку
    :param session: Сессия
    :raises GroupJoinRequestAlreadyResolvedException: 409. Возвращается если на приглашение пользователя уже отвечено
    :raises GroupJoinRequestNotFoundException: 404. Возвращается если приглашение пользователя не найдено
    :raises GroupIsFullException: 409. Возвращается если невозможно добавить в группу пользователя так как достигнуто максимальное количество
    :raises NotEnoughGroupPermissionsException: 403. Возвращается если недостаточно прав для изменения группы
    """

    # Загружаем и блокируем заявку, группу и участников
    join_request = (
        await session.execute(
            select(GroupJoinRequest)
            .join(GroupJoinRequest.requester)
            .join(User.user_profile)
            .where(GroupJoinRequest.id == join_request_id)
            .options(joinedload(GroupJoinRequest.group).selectinload(Group.members))
            .with_for_update(of=(GroupJoinRequest, Group, User, UserProfile))
        )
    ).scalar_one_or_none()

    if join_request is None:
        raise GroupJoinRequestNotFoundException()

    if join_request.status != JoinRequestStatus.PENDING:
        raise GroupJoinRequestAlreadyResolvedException()

    if len(join_request.group.members) >= join_request.group.max_members:
        raise GroupIsFullException()

    perm = (
        await session.execute(
            select(GroupUserPermission)
            .where(
                GroupUserPermission.group_id == join_request.group_id,
                GroupUserPermission.user_id == acceptor_id,
                GroupUserPermission.permission.in_(
                    [GroupPermission.ACCEPT_JOIN_REQUESTS, GroupPermission.FULL_ACCESS]
                ),
            )
            .with_for_update(of=GroupUserPermission)
        )
    ).scalar_one_or_none()

    if perm is None:
        raise NotEnoughGroupPermissionsException()

    if respond_status == JoinRequestStatus.APPROVED:
        await session.execute(
            (insert(GroupMember).values(group_id=join_request.group_id, user_id=join_request.requester_id))
        )
        join_request.status = JoinRequestStatus.APPROVED

    elif respond_status == JoinRequestStatus.REJECTED:
        join_request.status = JoinRequestStatus.REJECTED

    join_request_schema = await ObjectMapper.map(
        join_request, JoinRequestSchema, user_id=acceptor_id, session=session
    )
    await session.commit()
    return join_request_schema
