from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...user import User
from ..enums import InvitationStatus
from ..models import GroupInvitation, Group
from ..schemas import GroupInvitationSchema
from ..services import get_groups_member_count, get_groups_user_context
from ..services.group_service import map_to_group_invitation_schema


async def get_received_invitations(
    invitation_status: list[InvitationStatus] | None,
    limit: int,
    offset: int,
    invitee_id: UUID,
    session: AsyncSession,
) -> list[GroupInvitationSchema]:
    """
    Получение списка приглашений с фильтрацией
    :param offset: Смещение от начала выборки
    :param limit: Лимит возвращаемых значений за раз
    :param invitation_status: Статусы заявок
    :param invitee_id: ID приглашенного пользователя
    :param session: Сессия
    """

    stmt = (
        select(GroupInvitation)
        .options(
            joinedload(GroupInvitation.group).selectinload(Group.users).joinedload(User.user_profile)
        )
        .where(GroupInvitation.invitee_id == invitee_id)
        .order_by(GroupInvitation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if invitation_status:
        stmt = stmt.where(GroupInvitation.status.in_(invitation_status))

    invitations = (await session.execute(stmt)).scalars().all()

    groups_seq = [invitation.group for invitation in invitations]

    groups_user_context_map = await get_groups_user_context(
        groups_seq, invitee_id, session
    )

    members_count = await get_groups_member_count(groups_seq, session)

    return [
        map_to_group_invitation_schema(
            invitation,
            groups_user_context_map[invitation.group.id],
            members_count[invitation.group.id],
        )
        for invitation in invitations
    ]
