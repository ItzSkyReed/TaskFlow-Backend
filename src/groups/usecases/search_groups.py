from uuid import UUID

from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from ..models import Group
from ..schemas import GroupSearchSchema
from ..services import get_groups_user_context, get_groups_member_count, map_to_group_search_schema

async def search_groups(
    user_id: UUID,
    name: str,
    limit: int,
    offset: int,
    session: AsyncSession,
) -> list[GroupSearchSchema]:
    """
    Поиск групп по имени
    :param user_id: UUID пользователя вызывающего эндпоинт
    :param name: Строка для поиска по имени
    :param limit: лимит для поиска (максимальное число групп найденных за раз)
    :param offset: Смещение от "топа" похожих групп
    :param session: Сессия
    """

    await session.execute(
        select(func.set_config("pg_trgm.similarity_threshold", "0.1", True))
    )

    similarity_score = func.similarity(Group.name, name)

    ilike_priority = case(
        (Group.name.ilike(f"{name}%"), 2),  # начинается с name
        (Group.name.ilike(f"%{name}%"), 0),  # содержит name
        else_=1,
    )

    query = (
        select(Group)
        .options(
            load_only(
                Group.id,
                Group.name,
                Group.max_members,
                Group.has_avatar,
                Group.creator_id,
            ),
        )
        .where(
            or_(
                Group.name.op("%")(name),  # триграммы
                Group.name.ilike(f"{name}%"),
                Group.name.ilike(f"%{name}%"),
            )
        )
        .order_by(desc(ilike_priority), desc(similarity_score))
        .limit(limit)
        .offset(offset)
    )

    groups = (await session.execute(query)).scalars().all()
    if not groups:
        return []

    groups_user_context_map = await get_groups_user_context(groups, user_id, session)

    members_count = await get_groups_member_count(groups, session)

    return [
        map_to_group_search_schema(
            group, groups_user_context_map[group.id], members_count[group.id]
        )
        for group in groups
    ]
