from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...user.models import User
from ..exceptions import (
    GroupNotFoundException,
    NotEnoughGroupPermissionsException,
)
from ..models import Group


async def delete_group(
    group_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> None:
    """
    Удаление группы
    :param group_id: UUID удаляемой группы
    :param user_id: UUID человека, который удаляет группу
    :param session: Сессия.
    :raises GroupNotFoundException: 404 Группа не найдена
    :raises NotEnoughGroupPermissionsException: 403 Недостаточно прав на удаление группы (пользователь не является овнером)
    """
    user = (await session.execute(select(User).where(User.id == user_id))).scalar_one()

    deleted_group: Group = (
        await session.execute(select(Group).where(Group.id == group_id))
    ).scalar_one_or_none()

    if deleted_group is None:
        raise GroupNotFoundException()

    if deleted_group.creator_id != user.id:
        raise NotEnoughGroupPermissionsException()

    await session.execute(delete(Group).where(Group.id == group_id))
    await session.commit()
    return None
