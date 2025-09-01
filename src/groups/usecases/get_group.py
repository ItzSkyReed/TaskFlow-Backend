from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_pydantic_mapper import ObjectMapper

from ..schemas import GroupDetailSchema
from ..services import (
    get_group_with_members,
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

    return await ObjectMapper.map(
        group, GroupDetailSchema, user_id=user_id, session=session
    )
