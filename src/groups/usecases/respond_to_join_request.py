from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User
from ..exceptions import (
    GroupIsFullException,
    GroupJoinRequestAlreadyResolvedException,
    GroupJoinRequestNotFoundException,
    NotEnoughGroupPermissionsException,
)
from ..models import (
    Group,
    GroupJoinRequest,
    GroupMember,
    GroupPermission,
    JoinRequestStatus,
)
from ..schemas import (
    JoinRequestSchema,
)
from ..services import group_member_has_permission


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

    # Загружаем и блокируем заявку, группу
    join_request: GroupJoinRequest = (
        await session.execute(
            select(GroupJoinRequest)
            .join(GroupJoinRequest.group)
            .where(GroupJoinRequest.id == join_request_id)
            .options(
                contains_eager(GroupJoinRequest.group).selectinload(Group.members),
                joinedload(GroupJoinRequest.requester).joinedload(User.user_profile),
            )
            .with_for_update(of=(GroupJoinRequest, Group))
        )
    ).scalar_one_or_none()

    if join_request is None:
        raise GroupJoinRequestNotFoundException()

    if join_request.status != JoinRequestStatus.PENDING:
        raise GroupJoinRequestAlreadyResolvedException()

    if len(join_request.group.members) >= join_request.group.max_members:
        raise GroupIsFullException()

    if acceptor_id != join_request.group.creator_id:
        if not await group_member_has_permission(
            join_request.group.id,
            acceptor_id,
            session,
            GroupPermission.ACCEPT_JOIN_REQUESTS,
            GroupPermission.FULL_ACCESS,
        ):
            raise NotEnoughGroupPermissionsException()

    if respond_status == JoinRequestStatus.ACCEPTED:
        await session.execute(
            (insert(GroupMember).values(group_id=join_request.group_id, user_id=join_request.requester_id))
        )
        join_request.status = respond_status
    else:
        join_request.status = JoinRequestStatus.REJECTED

    join_request_schema: JoinRequestSchema = await ObjectMapper.map(
        join_request, JoinRequestSchema, user_id=acceptor_id, session=session
    )
    await session.commit()
    return join_request_schema
