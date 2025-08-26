from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...groups.schemas import GroupSummarySchema
from ...groups.services import get_groups_user_context
from ...user.exceptions import UserNotFoundByIdException
from ...user.models import User
from ..services.group_service import (
    get_groups_member_count,
    map_to_group_summary_schema,
)


async def get_user_groups(
    user_id: UUID,
    session: AsyncSession,
) -> list[GroupSummarySchema]:
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
        raise UserNotFoundByIdException()

    if not user.groups:
        return []

    groups_user_context_map = await get_groups_user_context(
        user.groups, user_id, session
    )

    members_count = await get_groups_member_count(user.groups, session)

    return [
        map_to_group_summary_schema(
            group, groups_user_context_map[group.id], members_count[group.id]
        )
        for group in user.groups
    ]
