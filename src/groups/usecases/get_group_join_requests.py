from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User
from .. import GroupJoinRequest
from ..enums import GroupPermission, JoinRequestStatus
from ..exceptions import GroupNotFoundException, NotEnoughGroupPermissionsException
from ..models import Group, GroupInvitation, GroupMember, GroupUserPermission
from ..schemas import JoinRequestSchema


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
    if not (await session.execute(select(exists().where(Group.id == group_id)))).scalar():
        raise GroupNotFoundException()

    # Проверяем, что пользователь в группе, и у него есть необходимые для просмотра права, если этого нет, не даем смотреть заявки.
    if not (
        await session.execute(
            select(GroupMember)
            .join(
                GroupUserPermission,
                and_(
                    GroupUserPermission.user_id == user_id,
                    GroupUserPermission.group_id == group_id,
                ),
                isouter=True,  # outer join, чтобы не потерять creator
            )
            .join(Group, Group.id == GroupMember.group_id)
            .where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                or_(
                    GroupUserPermission.permission == GroupPermission.FULL_ACCESS,
                    GroupUserPermission.permission == GroupPermission.ACCEPT_JOIN_REQUESTS,
                    Group.creator_id == user_id,  # проверка на создателя
                ),
            )
            .with_for_update()
        )
    ).scalar_one_or_none():
        raise NotEnoughGroupPermissionsException()

    stmt = (
        select(GroupJoinRequest)
        .options(joinedload(GroupJoinRequest.group).selectinload(Group.users).joinedload(User.user_profile))
        .where(GroupJoinRequest.group_id == group_id)
        .order_by(GroupJoinRequest.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if join_request_status:
        stmt = stmt.where(GroupInvitation.status.in_(join_request_status))

    join_requests = (await session.execute(stmt)).scalars().all()

    if not join_requests:
        return []

    return await ObjectMapper.map_bulk(join_requests, JoinRequestSchema, user_id=user_id, session=session)
