from typing import Sequence
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User
from ..enums import GroupPermission, JoinRequestStatus
from ..exceptions import GroupNotFoundException, NotEnoughGroupPermissionsException
from ..models import Group, GroupJoinRequest, GroupMember
from ..schemas import JoinRequestSchema
from ..services import group_member_has_permission


async def get_group_join_requests(
    join_request_status: list[JoinRequestStatus] | None,
    limit: int,
    offset: int,
    group_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> Sequence[JoinRequestSchema]:
    """
    Получение списка приглашений с фильтрацией
    :param user_id: Пользователь, получающий приглашения
    :param offset: Смещение от начала выборки
    :param limit: Лимит возвращаемых значений за раз
    :param join_request_status: Статусы заявок
    :param group_id: ID группы
    :param session: Сессия

    :raises NotEnoughGroupPermissionsException: 403. Возвращается если недостаточно прав для изменения ресурса
    """
    group: Group = (await session.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()

    if group is None:
        raise GroupNotFoundException()

    # Проверяем, что пользователь в группе, и у него есть необходимые для просмотра права, если этого нет, не даем смотреть заявки.
    if user_id != group.creator_id:
        if not (
            await session.execute(
                select(exists().where(GroupMember.group_id == group_id, GroupMember.user_id == user_id))
            )
        ).scalar_one_or_none() or not await group_member_has_permission(
            group_id, user_id, session, GroupPermission.FULL_ACCESS, GroupPermission.ACCEPT_JOIN_REQUESTS
        ):
            raise NotEnoughGroupPermissionsException()

    join_requests_query = (
        select(GroupJoinRequest)
        .options(
            joinedload(GroupJoinRequest.group).selectinload(Group.users).joinedload(User.user_profile),
            joinedload(GroupJoinRequest.requester).joinedload(User.user_profile),
        )
        .where(GroupJoinRequest.group_id == group_id)
        .order_by(GroupJoinRequest.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if join_request_status:
        join_requests_query = join_requests_query.where(GroupJoinRequest.status.in_(join_request_status))

    join_requests = (await session.execute(join_requests_query)).scalars().all()

    if not join_requests:
        return []

    return await ObjectMapper.map_bulk(join_requests, JoinRequestSchema, user_id=user_id, session=session)
