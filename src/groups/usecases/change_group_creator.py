from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user import User
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

    group = await get_group_with_members(group_id, session, with_for_update=True)

    if group.creator_id != actual_creator_user_id:
        raise NotEnoughGroupPermissionsException()

    # Заблокировать обоих пользователей (одним запросом)
    (
        (
            await session.execute(
                select(User)
                .where(User.id.in_([actual_creator_user_id, new_creator_user_id]))
                .with_for_update()
            )
        )
        .scalars()
        .all()
    )

    is_new_creator_in_group = await session.scalar(
        select(
            exists().where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == new_creator_user_id,
            )
        )
    )

    if not is_new_creator_in_group:
        raise RequiredUserNotInGroupException(new_creator_user_id)

    group.creator_id = new_creator_user_id

    schemas = await ObjectMapper.map(
        group, GroupDetailSchema, user_id=actual_creator_user_id, session=session
    )
    await session.commit()
    return schemas
