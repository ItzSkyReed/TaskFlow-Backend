from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...user.models import User
from ..enums import GroupPermission
from ..exceptions import (
    NotEnoughGroupPermissionsException,
    RequiredUserNotInGroupException,
    UserCantChangeOwnPermissionException,
)
from ..models import GroupMember, GroupUserPermission
from ..schemas import GroupMemberSchema
from ..services import get_group_with_members


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
    - Для изменения любого права нужно MANAGE_MEMBERS.
    - Для выдачи MANAGE_MEMBERS нужно FULL_ACCESS.
    - Для выдачи FULL_ACCESS нужно быть создателем группы.

    """

    # noinspection DuplicatedCode
    if target_user_id == changer_user_id:
        raise UserCantChangeOwnPermissionException()

    # Получаем группу с членами
    group = await get_group_with_members(group_id, session, with_for_update=True)

    if (
        permission == GroupPermission.FULL_ACCESS
        and changer_user_id != group.creator_id
    ):
        raise NotEnoughGroupPermissionsException()

    # Получаем права того, кто меняет права
    changer_member = (
        (
            await session.execute(
                select(GroupMember)
                .where(
                    GroupMember.user_id == changer_user_id,
                    GroupMember.group_id == group.id,
                )
                .options(joinedload(GroupMember.permission_objs))
                .with_for_update()
            )
        )
        .scalars()
        .one_or_none()
    )
    if not changer_member:
        raise RequiredUserNotInGroupException(user_id=changer_user_id)
    target_member = (
        (
            await session.execute(
                select(GroupMember)
                .where(
                    GroupMember.user_id == target_user_id,
                    GroupMember.group_id == group.id,
                )
                .options(joinedload(GroupMember.user).joinedload(User.user_profile))
                .with_for_update()
            )
        )
        .scalars()
        .one_or_none()
    )
    if not target_member:
        raise RequiredUserNotInGroupException(user_id=target_user_id)

    if GroupPermission.MANAGE_MEMBERS not in changer_member.permissions:
        raise NotEnoughGroupPermissionsException()

    if (
        permission == GroupPermission.MANAGE_MEMBERS
        and GroupPermission.FULL_ACCESS not in changer_member.permissions
    ):
        raise NotEnoughGroupPermissionsException()

    target_member.permission_objs.append(
        GroupUserPermission(
            group_id=group.id,
            user_id=target_user_id,
            permission=permission,
            granted_by=changer_user_id,
        )
    )

    await session.commit()
    await session.refresh(target_member)

    return GroupMemberSchema.model_validate(target_member, from_attributes=True)
