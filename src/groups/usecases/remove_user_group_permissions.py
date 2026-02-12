from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..enums import GroupPermission
from ..exceptions import (
    NotEnoughGroupPermissionsException,
    RequiredUserNotInGroupException,
    UserCantChangeOwnPermissionException,
)
from ..models import GroupUserPermission
from ..schemas import GroupMemberSchema
from ..services import ensure_has_permission, get_group_member, get_group_with_members


async def remove_user_group_permission(
    permission: GroupPermission,
    group_id: UUID,
    target_user_id: UUID,
    changer_user_id: UUID,
    session: AsyncSession,
) -> GroupMemberSchema:
    """
    Отзыв права пользователя
    :param permission: Право, которое надо убрать у пользователя.
    :param group_id: UUID группы
    :param target_user_id: UUID человека, которому меняют права.
    :param changer_user_id: UUID человека, который меняет права
    :param session: Сессия
    Notes
    -----
    - Для изменения любого права нужно MANAGE_MEMBERS.
    - Для отзыва MANAGE_MEMBERS нужно FULL_ACCESS.
    - Для отзыва FULL_ACCESS нужно быть создателем группы.

    """

    # noinspection DuplicatedCode
    if target_user_id == changer_user_id:
        raise UserCantChangeOwnPermissionException()

    group = await get_group_with_members(group_id, session, with_for_update=True)

    if permission == GroupPermission.FULL_ACCESS and changer_user_id != group.creator_id:
        raise NotEnoughGroupPermissionsException()

    # Получаем права того, кто меняет права
    changer_member = await get_group_member(
        changer_user_id, group.id, session, with_for_update=True, with_permissions=True
    )
    if not changer_member:
        raise RequiredUserNotInGroupException(user_id=changer_user_id)

    target_member = await get_group_member(
        target_user_id, group.id, session, with_for_update=True, with_profile=True
    )

    if not target_member:
        raise RequiredUserNotInGroupException(user_id=target_user_id)

    ensure_has_permission(changer_member, group)

    await session.execute(
        delete(GroupUserPermission).where(
            GroupUserPermission.group_id == group.id,
            GroupUserPermission.user_id == target_user_id,
            GroupUserPermission.permission == permission,
        )
    )
    await session.refresh(target_member)
    await session.commit()

    return GroupMemberSchema.model_validate(target_member, from_attributes=True)
