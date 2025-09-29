from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...user import User
from .. import JoinRequestStatus
from ..exceptions import GroupNotFoundException
from ..models import (
    Group,
    GroupJoinRequest,
    GroupMember,
    GroupPermission,
    GroupUserPermission,
)
from ..schemas import (
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
        .options(selectinload(Group.members).selectinload(GroupMember.user).joinedload(User.user_profile))
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
    ).scalars().first() is not None


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

    mem_query = select(GroupMember.group_id).where(
        GroupMember.user_id == user_id, GroupMember.group_id.in_(group_ids)
    )
    mem_set = set((await session.execute(mem_query)).scalars().all())

    # Получаем permissions только для групп, где пользователь является членом
    member_ids = list(mem_set)
    perms_map = {}
    if member_ids:
        perm_query = (
            select(
                GroupUserPermission.group_id,
                func.array_agg(func.nullif(GroupUserPermission.permission, None))
                .filter(GroupUserPermission.permission.isnot(None))
                .label("permissions"),
            )
            .where(GroupUserPermission.user_id == user_id, GroupUserPermission.group_id.in_(member_ids))
            .group_by(GroupUserPermission.group_id)
        )
        perm_rows = (await session.execute(perm_query)).all()
        perms_map = {row.group_id: row.permissions or [] for row in perm_rows}

    # Проверяем отправленные заявки для групп, где пользователь не является членом
    not_member_ids = [g.id for g in groups if g.id not in mem_set]
    join_sent_set = set()
    if not_member_ids:
        join_query = select(GroupJoinRequest.group_id).where(
            and_(
                GroupJoinRequest.requester_id == user_id,
                GroupJoinRequest.group_id.in_(not_member_ids),
                GroupJoinRequest.status == JoinRequestStatus.PENDING,
            )
        )
        join_sent_set = set((await session.execute(join_query)).scalars().all())

    return {
        g.id: GroupUserContextSchema(
            permissions=perms_map.get(g.id, []),
            is_creator=(g.creator_id == user_id),
            is_member=(g.id in mem_set),
            is_join_request_sent=(g.id in join_sent_set),
        )
        for g in groups
    }


async def get_group_user_context(
    group: Group, user_id: UUID, session: AsyncSession
) -> GroupUserContextSchema:
    """
    Получает контекст пользователя в одной группе.

    :param group: Группа
    :param user_id: UUID пользователя для которого находится контекст
    :param session: Асинхронная сессия SQLAlchemy
    :return: Объект GroupUserContextSchema
    """

    # проверка членства
    mem_query = select(GroupMember.group_id).where(
        GroupMember.user_id == user_id, GroupMember.group_id == group.id
    )
    is_member = (await session.execute(mem_query)).scalar_one_or_none() is not None

    if is_member:
        perm_query = select(
            func.array_agg(GroupUserPermission.permission)
            .filter(GroupUserPermission.permission.isnot(None))
            .label("permissions")
        ).where(GroupUserPermission.user_id == user_id, GroupUserPermission.group_id == group.id)

        permissions: list[str] | None = (await session.execute(perm_query)).scalar_one_or_none()

        is_join_request_sent: bool = False

    else:
        is_join_request_sent = (
            await session.execute(
                select(
                    exists(GroupJoinRequest).where(
                        and_(
                            GroupJoinRequest.requester_id == user_id,
                            GroupJoinRequest.group_id == group.id,
                            GroupJoinRequest.status == JoinRequestStatus.PENDING,
                        )
                    )
                )
            )
        ).scalar_one()

        permissions: list[str] | None = None

    return GroupUserContextSchema(
        permissions=permissions or [],
        is_creator=(group.creator_id == user_id),
        is_member=is_member,
        is_join_request_sent=is_join_request_sent,
    )


async def get_groups_member_count(groups: Sequence[Group], session: AsyncSession) -> dict[UUID, int]:
    """
    Находит кол-во участников для всех переданных групп
    :param groups: группы, для которых нужно найти кол-во участников
    :param session: Сессия.
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


async def get_group_member_count(group: Group, session: AsyncSession) -> int:
    """
    Находит кол-во участников для одной группы.
    :param group: группа.
    :param session: Сессия
    :return: актуальное кол-во участников
    """
    query = select(func.count(GroupMember.user_id)).where(GroupMember.group_id == group.id)

    count = await session.scalar(query)
    return count or 0
