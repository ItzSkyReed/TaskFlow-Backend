from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User
from ..enums import InvitationStatus
from ..models import Group, GroupInvitation
from ..schemas import GroupInvitationSchema


async def get_received_invitations(
    invitation_status: list[InvitationStatus] | None,
    limit: int,
    offset: int,
    invitee_id: UUID,
    session: AsyncSession,
) -> Sequence[GroupInvitationSchema]:
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
        .options(joinedload(GroupInvitation.group).selectinload(Group.users).joinedload(User.user_profile))
        .where(GroupInvitation.invitee_id == invitee_id)
        .order_by(GroupInvitation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if invitation_status:
        stmt = stmt.where(GroupInvitation.status.in_(invitation_status))

    invitations = (await session.execute(stmt)).scalars().all()

    return await ObjectMapper.map_bulk(
        invitations, GroupInvitationSchema, user_id=invitee_id, session=session
    )
