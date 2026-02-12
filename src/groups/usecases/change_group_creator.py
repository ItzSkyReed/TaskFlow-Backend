from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User, UserNotFoundException
from ...utils import lock_rows
from .. import GroupMember
from ..exceptions import (
    CannotChangeCreatorToYourselfException,
    NotEnoughGroupPermissionsException,
    RequiredUserNotInGroupException,
)
from ..schemas import GroupDetailSchema
from ..services import (
    get_group_with_members,
)


async def change_group_creator(
    group_id: UUID,
    actual_creator_user_id: UUID,
    new_creator_user_id: UUID,
    session: AsyncSession,
) -> GroupDetailSchema:
    """
    Изменение владельца группы
    :param group_id: UUID группы
    :param actual_creator_user_id: UUID актуального владельца группы
    :param new_creator_user_id: UUID нового владельца группы
    :param session: Сессия
    :raises TooManyCreatedGroupsException: Слишком много групп создано данным пользователем (403)
    :raises GroupWithSuchNameAlreadyExistsException: Группа с таким названием уже есть (409)
    """

    if actual_creator_user_id == new_creator_user_id:
        raise CannotChangeCreatorToYourselfException()

    # Лочим пользователей
    await lock_rows(session, User, User.id == actual_creator_user_id)
    new_user = (await lock_rows(session, User, User.id == new_creator_user_id)).scalar_one_or_none()

    if not new_user:
        raise UserNotFoundException(new_creator_user_id)

    group = await get_group_with_members(group_id, session, with_for_update=True)

    if group.creator_id != actual_creator_user_id:
        raise NotEnoughGroupPermissionsException()

    new_creator = (
        await session.execute(
            select(GroupMember)
            .where(GroupMember.user_id == new_creator_user_id, GroupMember.group_id == group_id)
            .with_for_update()
        )
    ).scalar_one_or_none()

    if new_creator is None:
        raise RequiredUserNotInGroupException(new_creator_user_id)

    group.creator_id = new_creator_user_id

    schemas = await ObjectMapper.map(
        group, GroupDetailSchema, user_id=actual_creator_user_id, session=session
    )
    await session.commit()
    return schemas
