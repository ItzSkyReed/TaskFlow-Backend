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

    - KICK_MEMBERS может кикать всех, кроме FULL_ACCESS и CONTROL_MEMBERS
    - CONTROL_MEMBERS может кикать всех, кроме FULL_ACCESS
    - FULL_ACCESS может кикать всех, кроме создателя
    - Никто не может кикать создателя
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

    initiator_perms = initiator.permissions
    target_perms = user_to_kick.permissions

    # Проверяем уровень инициатора
    if GroupPermission.FULL_ACCESS in initiator_perms:
        pass  # FULL_ACCESS может кикать любого (кроме создателя, проверено выше)
    elif GroupPermission.CONTROL_MEMBERS in initiator_perms:
        if GroupPermission.FULL_ACCESS in target_perms:  # CONTROL_MEMBERS не может кикать FULL_ACCESS
            raise NotEnoughGroupPermissionsException()
    elif GroupPermission.KICK_MEMBERS in initiator_perms:
        if GroupPermission.FULL_ACCESS in target_perms or GroupPermission.CONTROL_MEMBERS in target_perms:
            raise NotEnoughGroupPermissionsException()  # KICK_MEMBERS не может кикать FULL_ACCESS и CONTROL_MEMBERS
    else:
        raise NotEnoughGroupPermissionsException()  # Ни одно право не даёт права кика

    await session.execute(
        delete(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_to_kick_id,
        )
    )
    await session.commit()
