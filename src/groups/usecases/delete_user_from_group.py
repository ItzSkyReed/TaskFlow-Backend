from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import (
    CannotKickGroupCreatorException,
    CannotKickYourselfException,
    GroupNotFoundException,
    NotEnoughGroupPermissionsException,
    RequiredUserNotInGroupException,
)
from ..models import Group, GroupMember, GroupPermission
from ..services import get_group_member


async def delete_user_from_group(
    group_id: UUID,
    initiator_id: UUID,
    user_to_kick_id: UUID,
    session: AsyncSession,
) -> None:
    """
    Удаление пользователя из группы
    :param group_id: UUID группы
    :param initiator_id: UUID человека, который кикает другого.
    :param user_to_kick_id: UUID человека, которого надо исключить из группы
    :param session: Сессия

    Notes
    -----
    - FULL_ACCESS может кикать всех, кроме создателя
    """

    if initiator_id == user_to_kick_id:
        raise CannotKickYourselfException()

    # Загружаем группу и блокируем на время операции
    group = (
        await session.execute(select(Group).where(Group.id == group_id).with_for_update())
    ).scalar_one_or_none()

    if not group:
        raise GroupNotFoundException()

    if group.creator_id == user_to_kick_id:
        raise CannotKickGroupCreatorException()

    user_to_kick = await get_group_member(
        user_to_kick_id, group.id, session, with_for_update=True, with_permissions=True
    )
    if not user_to_kick:
        raise RequiredUserNotInGroupException(user_id=user_to_kick_id)

    initiator = await get_group_member(
        initiator_id, group.id, session, with_for_update=True, with_profile=True
    )
    if not initiator:
        raise RequiredUserNotInGroupException(user_id=initiator_id)

    # Проверяем уровень инициатора и пользователя для кика
    if group.creator_id != initiator_id and (
        GroupPermission.FULL_ACCESS not in initiator.permissions
        or GroupPermission.FULL_ACCESS in user_to_kick.permissions
    ):
        raise NotEnoughGroupPermissionsException()

    await session.execute(
        delete(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_to_kick_id,
        )
    )
    await session.commit()
