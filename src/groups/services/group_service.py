from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from ...user import User
from ...user.schemas import PublicUserSchema
from ..exceptions import GroupNotFoundException
from ..models import (
    Group,
    GroupInvitation,
    GroupMember,
    GroupPermission,
    GroupUserPermission,
)
from ..schemas import (
    GroupDetailSchema,
    GroupInvitationSchema,
    GroupMemberSchema,
    GroupSearchSchema,
    GroupSummarySchema,
    GroupUserContextSchema,
)


async def get_group_with_members(
    group_id: UUID, session: AsyncSession, *, with_for_update: bool = False
) -> Group:
    """
    Возвращает группу с загруженными участниками (Юзерами, и их профилями)
    :param group_id: UUID группы
    :param session: Сессия
    :param with_for_update: Блокировка обновления
    :raises GroupNotFoundByIdException: (404) Если группы не существует
    """
    stmt = (
        select(Group)
        .where(Group.id == group_id)
        .options(
            selectinload(Group.members)
            .selectinload(GroupMember.user)
            .selectinload(User.user_profile)
        )
    )

    if with_for_update:
        stmt = stmt.with_for_update()

    group = (await session.execute(stmt)).scalar_one_or_none()
    if group is None:
        raise GroupNotFoundException()
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


async def get_groups_user_context(
    groups: Sequence[Group], user_id: UUID, session: AsyncSession
) -> dict[UUID, GroupUserContextSchema]:
    """
    :param groups: Группы
    :param user_id: UUID пользователя для которого находится контекст
    :param session: Сессия
    :return: Для каждой переданной группы возвращается словарь с UUID группы в виде ключа с заполненным ``GroupUserContextSchema`` классом
    """
    group_ids = [g.id for g in groups]
    GUP = aliased(GroupUserPermission)
    perm_query = (
        select(
            GUP.group_id,
            func.array_agg(func.nullif(GUP.permission, None))
            .filter(GUP.permission.isnot(None))
            .label("permissions"),
        )
        .where(GUP.user_id == user_id, GUP.group_id.in_(group_ids))
        .group_by(GUP.group_id)
    )
    perm_rows = (await session.execute(perm_query)).all()

    mem_query = select(GroupMember.group_id).where(
        GroupMember.user_id == user_id, GroupMember.group_id.in_(group_ids)
    )
    perms_map = {row.group_id: row.permissions or [] for row in perm_rows}
    mem_set = set((await session.execute(mem_query)).scalars().all())

    return {
        g.id: GroupUserContextSchema(
            permissions=perms_map.get(g.id, []),
            is_creator=(g.creator_id == user_id),
            is_member=(g.id in mem_set),
        )
        for g in groups
    }


async def get_groups_member_count(
    groups: Sequence[Group], session: AsyncSession
) -> dict[UUID, int]:
    """
    Находит кол-во участников для всех переданных групп
    :param groups: группы, для которых нужно найти кол-во участников
    :param session: Сессия
    :return: Возвращает словарь с ключем в виде UUID группы и значение в виде актуального кол-ва участников
    """

    query = (
        select(
            Group.id,
            func.coalesce(func.count(GroupMember.user_id), 0).label("member_count"),
        )
        .outerjoin(GroupMember, Group.id == GroupMember.group_id)
        .where(Group.id.in_([g.id for g in groups]))
        .group_by(Group.id)
    )

    rows = await session.execute(query)

    return {group_id: member_count for group_id, member_count in rows}


def map_to_group_detail_schema(
    group: Group, user_context: GroupUserContextSchema, group_members_count: int
) -> GroupDetailSchema:
    return GroupDetailSchema(
        id=group.id,
        name=group.name,
        description=group.description,
        creator_id=group.creator_id,
        created_at=group.created_at,
        max_members_count=group.max_members,
        members=[
            GroupMemberSchema.model_validate(member, from_attributes=True)
            for member in group.members
        ],
        has_avatar=group.has_avatar,
        me=user_context,
        members_count=group_members_count,
    )


def map_to_group_summary_schema(
    group: Group, user_context: GroupUserContextSchema, group_members_count
) -> GroupSummarySchema:
    return GroupSummarySchema(
        id=group.id,
        name=group.name,
        creator_id=group.creator_id,
        created_at=group.created_at,
        max_members_count=group.max_members,
        has_avatar=group.has_avatar,
        me=user_context,
        members_count=group_members_count,
    )


def map_to_group_search_schema(
    group: Group, user_context: GroupUserContextSchema, group_members_count
) -> GroupSearchSchema:
    return GroupSearchSchema(
        id=group.id,
        name=group.name,
        max_members_count=group.max_members,
        has_avatar=group.has_avatar,
        me=user_context,
        members_count=group_members_count,
    )


def map_to_group_invitation_schema(
    invitation: GroupInvitation,
    user_context: GroupUserContextSchema,
    group_members_count: int,
) -> GroupInvitationSchema:
    return GroupInvitationSchema(
        id=invitation.id,
        status=invitation.status,
        updated_at=invitation.updated_at,
        created_at=invitation.created_at,
        inviter=PublicUserSchema.model_validate(
            invitation.inviter, from_attributes=True
        ),
        group=map_to_group_summary_schema(
            invitation.group, user_context, group_members_count
        ),
    )
