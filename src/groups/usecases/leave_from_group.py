from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import (
    CreatorCantLeaveFromGroupException,
    GroupNotFoundException,
)
from ..models import Group, GroupMember


async def leave_from_group(
    group_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> None:
    """
    Удаление аватарки профиля группы
    :param group_id: UUID группы
    :param user_id: UUID человека, который выходит из группы
    :param session: Сессия
    """

    group = (
        await session.execute(select(Group).where(Group.id == group_id))
    ).scalar_one_or_none()

    if not group:
        raise GroupNotFoundException

    if group.creator_id == user_id:
        raise CreatorCantLeaveFromGroupException()

    await session.execute(
        delete(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == user_id)
    )
    await session.commit()
