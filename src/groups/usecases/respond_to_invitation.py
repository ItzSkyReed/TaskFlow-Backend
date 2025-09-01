from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User
from .. import GroupMember, InvitationStatus
from ..exceptions import GroupInvitationNotFoundException, GroupIsFullException
from ..models import Group, GroupInvitation
from ..schemas import GroupInvitationSchema, RespondToInvitationSchema


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
            .where(
                GroupInvitation.id == invitation_id,
                GroupInvitation.invitee_id == user_id,
            )
            .options(
                joinedload(GroupInvitation.group)
                .selectinload(Group.members)
                .joinedload(User.user_profile)
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

    return await ObjectMapper.map(invitation, GroupInvitationSchema, user_id=user_id, session=session)
