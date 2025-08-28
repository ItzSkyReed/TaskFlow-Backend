from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import InvitationStatus, GroupMember
from ..exceptions import GroupInvitationNotFoundException, GroupIsFullException
from ..models import GroupInvitation, Group
from ..schemas import GroupInvitationSchema, RespondToInvitationSchema
from ..services import get_groups_user_context, get_groups_member_count
from ..services.group_service import map_to_group_invitation_schema
from ...user import User


async def respond_to_invitation(
    respond_status: RespondToInvitationSchema,
    invitation_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> GroupInvitationSchema:
    """
    Получение списка приглашений с фильтрацией
    :param respond_status: Статус ответа на заявку: Принятие/отказ
    :param invitation_id: UUID приглашения
    :param user_id: UUID пользователя, отвечающего на приглашение
    :param session: Сессия
    """

    invitation = (
        await session.execute(
            select(GroupInvitation)
            .where(GroupInvitation.id == invitation_id, GroupInvitation.invitee_id == user_id)
            .options(
                joinedload(GroupInvitation.group).selectinload(Group.members).joinedload(User.user_profile)
            )
            .with_for_update(of=Group)
        )
    ).scalar_one_or_none()

    if invitation is None:
        raise GroupInvitationNotFoundException()

    if len(invitation.group.members) == invitation.group.max_members:
        raise GroupIsFullException()

    if respond_status.response.REJECTED:
        invitation.status = InvitationStatus.REJECTED
    else:
        invitation.status = InvitationStatus.ACCEPTED
        invitation.group.members.append(GroupMember(user_id=user_id))

    await session.commit()

    group_seq = [invitation.group]

    groups_user_context_map = await get_groups_user_context(
        group_seq, user_id, session
    )

    members_count = await get_groups_member_count(group_seq, session)

    return map_to_group_invitation_schema(invitation, groups_user_context_map[invitation.group.id], members_count[invitation.group.id])


