from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ...user.models import User
from ...utils import lock_rows
from ..enums import GroupPermission
from ..exceptions import (
    NotEnoughGroupPermissionsException,
    RequiredUserNotInGroupException,
    UserCantChangeOwnPermissionException,
)
from ..models import GroupUserPermission
from ..schemas import GroupMemberSchema
from ..services import ensure_has_permission, get_group_member, get_group_with_members


async def add_user_group_permission(
    permission: GroupPermission,
    group_id: UUID,
    target_user_id: UUID,
    changer_user_id: UUID,
    session: AsyncSession,
) -> GroupMemberSchema:
    """
    Добавление права пользователю
    :param permission: Право, которое надо добавить пользователю.
    :param group_id: UUID группы
    :param target_user_id: UUID человека, которому меняют права.
    :param changer_user_id: UUID человека, который меняет права
    :param session: Сессия
    Notes
    -----
    - Для изменения любого права нужно CONTROL_MEMBERS или FULL_ACCESS.
    - Для выдачи CONTROL_MEMBERS нужно FULL_ACCESS.
    - Для выдачи FULL_ACCESS нужно быть создателем группы.

    """
    # noinspection DuplicatedCode
    if target_user_id == changer_user_id:
        raise UserCantChangeOwnPermissionException()

    # Лочим пользователей
    await lock_rows(session, User, User.id.in_([target_user_id, changer_user_id]))

    # Получаем группу с членами
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

    ensure_has_permission(changer_member, group, permission)

    await session.execute(
        insert(GroupUserPermission)
        .values(group_id=group_id, user_id=target_user_id, permission=permission, granted_by=changer_user_id)
        .on_conflict_do_nothing(
            index_elements=[
                GroupUserPermission.user_id,
                GroupUserPermission.permission,
                GroupUserPermission.group_id,
            ]
        )
    )
    await session.refresh(target_member)
    await session.commit()

    return GroupMemberSchema.model_validate(target_member, from_attributes=True)
