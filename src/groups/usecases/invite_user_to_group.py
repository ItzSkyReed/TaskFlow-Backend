from uuid import UUID

from sqlalchemy import exists, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User, UserNotFoundException
from ..exceptions import (
    CannotInviteUserThatIsAlreadyInThatGroupException,
    CannotInviteYourselfException,
    GroupNotFoundException,
    NotEnoughGroupPermissionsException,
)
from ..models import (
    Group,
    GroupInvitation,
    GroupMember,
    GroupPermission,
    InvitationStatus,
)
from ..schemas import GroupInvitationSchema
from ..services import group_member_has_permission


async def invite_user_to_group(
    group_id: UUID,
    inviter_id: UUID,
    invitee_id: UUID,
    session: AsyncSession,
) -> GroupInvitationSchema:
    """
    Отправка приглашения пользователю в группу, если ранее его не было (или возврат ранее созданного, если было)
    :param invitee_id: ID приглашенного пользователя
    :param inviter_id: ID приглашающего пользователя
    :param group_id: ID группы куда приглашается пользователь
    :param session: Сессия
    """

    if invitee_id == inviter_id:
        raise CannotInviteYourselfException()

    group: Group = (await session.execute(select(Group).where(Group.id == group_id))).scalar_one_or_none()
    if group is None:
        raise GroupNotFoundException()

    if not (await session.execute(select(exists().where(User.id == invitee_id)))).scalar():
        raise UserNotFoundException(invitee_id)

    member_exists = (
        await session.execute(
            select(GroupMember).where(
                GroupMember.user_id == invitee_id,
                GroupMember.group_id == group_id,
            )
        )
    ).scalar()

    if member_exists:
        raise CannotInviteUserThatIsAlreadyInThatGroupException()

    if inviter_id != group.creator_id:
        if not await group_member_has_permission(
            group_id,
            inviter_id,
            session,
            GroupPermission.FULL_ACCESS,
            GroupPermission.INVITE_MEMBERS,
        ):
            raise NotEnoughGroupPermissionsException()

    stmt = (
        insert(GroupInvitation)
        .values(
            group_id=group_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
        )
        .on_conflict_do_nothing(
            index_elements=["group_id", "invitee_id"],
            index_where=(GroupInvitation.status == literal(InvitationStatus.PENDING, literal_execute=True)),
        )
    )

    await session.execute(stmt)

    invitation = (
        await session.execute(
            select(GroupInvitation)
            .join(Group, Group.id == GroupInvitation.group_id)
            .where(
                GroupInvitation.group_id == group_id,
                GroupInvitation.invitee_id == invitee_id,
                GroupInvitation.status == InvitationStatus.PENDING,
            )
            .with_for_update(of=Group)
            .options(
                contains_eager(GroupInvitation.group).selectinload(Group.users).joinedload(User.user_profile)
            )
        )
    ).scalar_one()

    schema = await ObjectMapper.map(invitation, GroupInvitationSchema, user_id=inviter_id, session=session)
    await session.commit()
    return schema
