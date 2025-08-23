from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import GroupDetailSchema
from ..services import get_group_with_members


async def get_group(
    group_id: UUID,
    session: AsyncSession,
) -> GroupDetailSchema:
    """
    Получение группы по ID.
    :param group_id: ID группы
    :param session: Сессия
    """

    return GroupDetailSchema.model_validate(
        await get_group_with_members(group_id, session), from_attributes=True
    )
