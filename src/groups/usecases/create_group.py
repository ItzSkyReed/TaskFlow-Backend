from uuid import UUID

from asyncpg import UniqueViolationError
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ...user.models import User
from ..constants import MAX_CREATED_GROUPS
from ..exceptions import TooManyCreatedGroupsException, GroupWithSuchNameAlreadyExistsException
from ..models import Group, GroupInvitation, GroupMember, InvitationStatus
from ..schemas import CreateGroupSchema, GroupDetailSchema
from ..services import get_group_with_members


async def create_group(
    created_group: CreateGroupSchema,
    user_id: UUID,
    session: AsyncSession,
) -> GroupDetailSchema:
    """
    Создание группы
    :param created_group: Создаваемая группа
    :param user_id: UUID профиля
    :param session: Сессия
    """
    user = (
        await session.execute(select(User).where(User.id == user_id).with_for_update())
    ).scalar_one()

    created_count = (
        await session.execute(
            select(func.count(Group.id)).where(Group.creator_id == user_id)
        )
    ).scalar_one()
    if created_count >= MAX_CREATED_GROUPS:
        raise TooManyCreatedGroupsException()

    group = Group(
        name=created_group.name,
        creator_id=user.id,
        max_members=created_group.max_members,
        description=created_group.description,
    )
    session.add(group)

    try:
        await session.flush()
    except IntegrityError as err:
        await session.rollback()
        if getattr(err.orig, 'pgcode', None) == '23505':
            raise GroupWithSuchNameAlreadyExistsException(
                group_name=created_group.name
            ) from err
        raise # pragma: no cover

    creator_membership = GroupMember(user=user, group=group)
    session.add(creator_membership)

    await session.flush()

    if created_group.invitations:
        invitations_to_add: list[dict] = [
            {
                "group_id": group.id,
                "inviter_id": user_id,
                "invitee_id": invitee_id,
                # статус по умолчанию PENDING предполагается на уровне БД
            }
            for invitee_id in created_group.invitations
        ]
        stmt = insert(GroupInvitation).values(invitations_to_add)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["group_id", "invitee_id"],
            index_where=(GroupInvitation.status == InvitationStatus.PENDING),
        )
        await session.execute(stmt)
    await session.commit()

    group = await get_group_with_members(group.id, session)

    return GroupDetailSchema.model_validate(group, from_attributes=True)
