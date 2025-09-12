from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import (
    CannotKickGroupCreatorException,
    CannotKickYourselfException,
    GroupNotFoundException,
    NotEnoughGroupPermissionsException,
)
from ..models import Group, GroupMember, GroupPermission
from ..services import group_member_has_permission


async def delete_user_from_group(
    group_id: UUID,
    initiator_id: UUID,
    user_to_kick_id: UUID,
    session: AsyncSession,
) -> None:
    """
    Удаление аватарки профиля группы
    :param group_id: UUID группы
    :param initiator_id: UUID человека, который кикает другого.
    :param user_to_kick_id: UUID человека, которого надо исключить из группы
    :param session: Сессия
    """

    group = (await session.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()

    if not group:
        raise GroupNotFoundException

    if initiator_id == user_to_kick_id:
        raise CannotKickYourselfException()

    if group.creator_id == user_to_kick_id:
        raise CannotKickGroupCreatorException()

    if initiator_id != group.creator_id:
        if not group_member_has_permission(
            group_id,
            initiator_id,
            session,
            GroupPermission.FULL_ACCESS,
            GroupPermission.KICK_MEMBERS,
        ):
            raise NotEnoughGroupPermissionsException()

    await session.execute(
        delete(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == user_to_kick_id)
    )
    await session.commit()
