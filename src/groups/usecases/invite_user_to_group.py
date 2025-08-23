from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import (
    CannotInviteYourselfException,
    CannotUserThatIsAlreadyInThatGroupException,
    GroupNotFoundByIdException,
    NotEnoughPermissionsException,
)
from ..models import (
    Group,
    GroupInvitation,
    GroupMember,
    GroupPermission,
    InvitationStatus,
)
from ..schemas import InvitationSummarySchema
from ..services import group_member_has_permission


async def invite_user_to_group(
    group_id: UUID,
    inviter_id: UUID,
    invitee_id: UUID,
    session: AsyncSession,
) -> InvitationSummarySchema:
    """
    Отправка приглашения пользователю в группу, если ранее его не было (или возврат ранее созданного, если было)
    :param invitee_id: ID приглашенного пользователя
    :param inviter_id: ID приглашающего пользователя
    :param group_id: ID группы куда приглашается пользователь
    :param session: Сессия
    """

    if invitee_id == inviter_id:
        raise CannotInviteYourselfException()

    if not (
        await session.execute(select(exists().where(Group.id == group_id)))
    ).scalar():
        raise GroupNotFoundByIdException()

    member_exists = (
        await session.execute(
            select(GroupMember)
            .where(
                GroupMember.user_id == invitee_id,
                GroupMember.group_id == group_id,
            )
            .with_for_update()
        )
    ).scalar()

    if member_exists:
        raise CannotUserThatIsAlreadyInThatGroupException()

    if not group_member_has_permission(
        group_id,
        inviter_id,
        session,
        GroupPermission.FULL_ACCESS,
        GroupPermission.INVITE_MEMBERS,
    ):
        raise NotEnoughPermissionsException()

    stmt = (
        insert(GroupInvitation)
        .values(
            group_id=group_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
        )
        .on_conflict_do_nothing(
            index_elements=["group_id", "invitee_id"],
            index_where=(GroupInvitation.status == InvitationStatus.PENDING),
        )
    )

    await session.execute(stmt)

    invitation = (
        await session.execute(
            select(GroupInvitation).where(
                GroupInvitation.group_id == group_id,
                GroupInvitation.invitee_id == invitee_id,
                GroupInvitation.status == InvitationStatus.PENDING,
            )
        )
    ).scalar_one()

    await session.commit()

    return InvitationSummarySchema.model_validate(invitation, from_attributes=True)
