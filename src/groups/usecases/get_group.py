from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import GroupDetailSchema
from ..services import (
    get_group_with_members,
    get_groups_member_count,
    get_groups_user_context,
    map_to_group_detail_schema,
)


async def get_group(
    group_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> GroupDetailSchema:
    """
    Получение группы по ID.
    :param user_id: UUID пользователя для которого находится контекст группы
    :param group_id: ID группы
    :param session: Сессия
    """
    group = await get_group_with_members(group_id, session)

    group_seq = [group]

    groups_user_context_map = await get_groups_user_context(group_seq, user_id, session)

    members_count = await get_groups_member_count(group_seq, session)

    return map_to_group_detail_schema(
        group, groups_user_context_map[group.id], members_count[group.id]
    )
