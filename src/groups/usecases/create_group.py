from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...user import User, UserNotFoundByIdException
from ..constants import MAX_CREATED_GROUPS
from ..exceptions import TooManyCreatedGroupsException
from ..models import Group, GroupInvitation, GroupMembers, InvitationStatus
from ..schemas import CreateGroupSchema, GroupSchema


async def create_group(
    created_group: CreateGroupSchema,
    user_id: UUID,
    session: AsyncSession,
) -> GroupSchema:
    """
    Обновление своего профиля
    :param created_group: Создаваемая группа
    :param user_id: UUID профиля
    :param session: Сессия
    """
    user = (
        await session.execute(select(User).where(User.id == user_id).with_for_update())
    ).scalar_one_or_none()
    if user is None:
        raise UserNotFoundByIdException()

    created_count = (
        await session.execute(
            select(func.count(Group.id)).where(Group.creator_id == user_id)
        )
    ).scalar_one()
    if created_count >= MAX_CREATED_GROUPS:
        raise TooManyCreatedGroupsException()

    group = Group(name=created_group.name, creator_id=user.id)
    session.add(group)

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
            where=(GroupInvitation.status == InvitationStatus.PENDING),
        )
        await session.execute(stmt)
    await session.commit()

    group = (
        await session.execute(
            select(Group)
            .where(Group.id == group.id)
            .options(
                selectinload(Group.members)
                .selectinload(GroupMembers.user)
                .selectinload(User.user_profile)
            )
        )
    ).scalar_one()

    return GroupSchema.model_validate(group, from_attributes=True)
