from uuid import UUID

from sqlalchemy import exists, func, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ...exceptions import SomethingWentWrongException
from ...utils import lock_rows
from ..exceptions import (
    GroupIsFullException,
    GroupNotFoundException,
    UserAlreadyInGroupRequestException,
)
from ..models import (
    Group,
    GroupJoinRequest,
    GroupMember,
)
from ..schemas import JoinRequestSchema


async def send_join_request(
    group_id: UUID,
    requester_id: UUID,
    session: AsyncSession,
) -> JoinRequestSchema:
    """
    Отправка запроса на вступление в группу
    :param requester_id: ID пользователя отправляющего заявку в группу
    :param group_id: ID группы, в которую пользователь отправляет заявку
    :param session: Сессия
    """

    if not (await lock_rows(session, Group, Group.id == group_id)).scalar_one_or_none():
        raise GroupNotFoundException()

    await lock_rows(session, GroupMember, GroupMember.group_id == group_id)

    try:
        if (
            await session.execute(
                select(exists().where(GroupMember.user_id == requester_id, Group.id == group_id))
            )
        ).scalar():
            raise UserAlreadyInGroupRequestException()
    except IntegrityError as err:
        raise SomethingWentWrongException() from err

    # Проверяем кол-во участников
    subq = (
        select(Group.id.label("group_id"))
        .join(GroupMember, Group.id == GroupMember.group_id, isouter=True)
        .where(Group.id == group_id)
        .group_by(Group.id, Group.max_members)
        .having(func.count(GroupMember.user_id) < Group.max_members)
    )

    # Вставка заявки с возвратом результата
    stmt = (
        insert(GroupJoinRequest)
        .from_select(["group_id", "requester_id"], select(subq.c.group_id, literal(requester_id)))
        .on_conflict_do_nothing(index_elements=["group_id", "requester_id"])
        .returning(GroupJoinRequest)
    )
    try:
        result = await session.execute(stmt)
    except IntegrityError as err:
        raise SomethingWentWrongException() from err

    inserted_row = result.scalar_one_or_none()

    if inserted_row is None:
        existing = await session.execute(
            select(GroupJoinRequest).where(
                GroupJoinRequest.group_id == group_id,
                GroupJoinRequest.requester_id == requester_id,
            )
        )
        if existing.scalar_one_or_none():
            await session.commit()
            return JoinRequestSchema.model_validate(existing, from_attributes=True)

        raise GroupIsFullException()

    await session.commit()
    return JoinRequestSchema.model_validate(inserted_row, from_attributes=True)
