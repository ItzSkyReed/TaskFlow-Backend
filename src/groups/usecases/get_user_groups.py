from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...groups.schemas import GroupSummarySchema
from ...user.exceptions import UserNotFoundException
from ...user.models import User


async def get_user_groups(
    user_id: UUID,
    session: AsyncSession,
) -> Sequence[GroupSummarySchema]:
    """
    Получение списка групп, где состоит пользователь.
    :param user_id: ID пользователя
    :param session: Сессия
    """

    user = (
        (
            await session.execute(
                select(User).where(user_id == User.id).options(joinedload(User.groups))
            )
        )
        .unique()
        .scalar_one_or_none()
    )

    if user is None:
        raise UserNotFoundException(user_id)

    if not user.groups:
        return []

    return await ObjectMapper.map_bulk(
        user.group, GroupSummarySchema, user_id=user_id, session=session
    )
