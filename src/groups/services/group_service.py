from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...user import User
from ..exceptions import GroupNotFoundByIdException
from ..models import Group, GroupMember, GroupPermission, GroupUserPermission


async def get_group_with_members(group_id: UUID, session: AsyncSession) -> Group:
    group = (
        await session.execute(
            select(Group)
            .where(Group.id == group_id)
            .options(
                selectinload(Group.members)
                .selectinload(GroupMember.user)
                .selectinload(User.user_profile)
            )
        )
    ).scalar_one_or_none()
    if group is None:
        raise GroupNotFoundByIdException()
    return group


async def group_member_has_permission(
    group_id: UUID, user_id: UUID, session: AsyncSession, *permissions: GroupPermission
) -> bool:
    return (
        await session.execute(
            (
                select(GroupUserPermission).where(
                    GroupUserPermission.group_id == group_id,
                    GroupUserPermission.user_id == user_id,
                    GroupUserPermission.permission.in_(permissions),
                )
            )
        )
    ) is not None
