from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .. import GroupPermission
from ..exceptions import (
    GroupSizeConflictException,
    GroupWithSuchNameAlreadyExistsException,
    NotEnoughGroupPermissionsException,
)
from ..schemas import GroupDetailSchema, PatchGroupSchema
from ..services import (
    get_group_with_members,
    get_groups_member_count,
    get_groups_user_context,
    group_member_has_permission,
    map_to_group_detail_schema,
)


async def patch_group(
    group_id: UUID,
    patched_group: PatchGroupSchema,
    initiator_id: UUID,
    session: AsyncSession,
) -> GroupDetailSchema:
    """
    Создание группы
    :param group_id: UUID изменяемой группы
    :param patched_group: Поля для изменения в грыппе
    :param initiator_id: UUID пользователя вызывающего изменения группы
    :param session: Сессия
    :raises GroupWithSuchNameAlreadyExistsException: Группа с таким названием уже есть (409)
    :raises GroupWithSuchNameAlreadyExistsException: C
    """
    group = await get_group_with_members(group_id, session, with_for_update=True)

    if patched_group.max_members_count is not None:
        if patched_group.max_members_count < len(group.members):
            raise GroupSizeConflictException(
                current_members=len(group.members),
                requested_size=patched_group.max_members_count,
            )
        group.max_members = patched_group.max_members_count

    if initiator_id != group.creator_id:
        if not group_member_has_permission(
            group_id,
            initiator_id,
            session,
            GroupPermission.FULL_ACCESS,
            GroupPermission.MANAGE_GROUP,
        ):
            raise NotEnoughGroupPermissionsException()

    if patched_group.name:
        group.name = patched_group.name

    if patched_group.description:
        group.description = patched_group.description

    try:
        await session.flush()
    except IntegrityError as err:
        await session.rollback()
        if getattr(err.orig, "pgcode", None) == "23505":
            # asyncpg UniqueViolationError;
            uq_err = err.orig.__cause__  # ty: ignore[possibly-unbound-attribute]
            if uq_err.constraint_name == "ix_groups_name":  # ty: ignore[unresolved-attribute]
                raise GroupWithSuchNameAlreadyExistsException(
                    group_name=patched_group.name # ty: ignore[invalid-argument-type]
                ) from err
        raise  # pragma: no cover

    await session.commit()
    group_seq = [group]
    groups_user_context_map = await get_groups_user_context(
        group_seq, initiator_id, session
    )

    members_count = await get_groups_member_count(group_seq, session)

    return map_to_group_detail_schema(
        group, groups_user_context_map[group.id], members_count[group.id]
    )
