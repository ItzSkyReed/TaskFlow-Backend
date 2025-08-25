import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import User, UserNotFoundByIdException
from ...groups.schemas import GroupSummarySchema


async def get_user_groups(
        user_id: UUID,
        session: AsyncSession,
) -> list[GroupSummarySchema]:
    """
    Получение списка групп, где состоит пользователь.
    :param user_id: ID пользователя
    :param session: Сессия
    """

    user = (await session.execute(
        select(User)
        .where(User.id == user_id)
        .options(joinedload(User.groups))
    )).unique().scalar_one_or_none()

    if user is None:
        raise UserNotFoundByIdException()
    return [
        GroupSummarySchema.model_validate(group, from_attributes=True)
        for group in user.groups
    ]
