from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...user import User
from ..enums import InvitationStatus
from ..models import GroupInvitation
from ..schemas import ReceivedInvitationSchema


async def get_received_invitations(
    invitation_status: list[InvitationStatus] | None,
    limit: int,
    offset: int,
    invitee_id: UUID,
    session: AsyncSession,
) -> list[ReceivedInvitationSchema]:
    """
    Получение списка приглашений с фильтрацией
    :param offset: Смещение от начала выборки
    :param limit: Лимит возвращаемых значений за раз
    :param invitation_status: Статусы заявок
    :param invitee_id: ID группы
    :param session: Сессия
    """

    stmt = (
        select(GroupInvitation)
        .options(
            joinedload(GroupInvitation.group),
            joinedload(GroupInvitation.inviter).joinedload(User.user_profile),
        )
        .where(GroupInvitation.invitee_id == invitee_id)
        .order_by(GroupInvitation.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if invitation_status:
        stmt = stmt.where(GroupInvitation.status.in_(invitation_status))

    result = (await session.execute(stmt)).scalars().all()

    # Преобразуем в Pydantic-схему
    invitations = [
        ReceivedInvitationSchema.model_validate(inv, from_attributes=True)
        for inv in result
    ]
    return invitations
