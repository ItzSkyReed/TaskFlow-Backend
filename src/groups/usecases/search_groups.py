import logging

from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from ..models import Group
from ..schemas import GroupSearchSchema


async def search_groups(
    name: str,
    limit: int,
    offset: int,
    session: AsyncSession,
) -> list[GroupSearchSchema]:
    """
    Поиск групп по имени
    :param name: Строка для поиска по имени
    :param limit: лимит для поиска (макс. число групп найденных за раз)
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
            load_only(Group.id, Group.name, Group.max_members, Group.has_avatar),
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

    result = await session.execute(query)
    groups_with_scores = result.scalars().all()
    logging.warning(f"{groups_with_scores, groups_with_scores[0]}")
    return [
        GroupSearchSchema.model_validate(group, from_attributes=True)
        for group in groups_with_scores
    ]
