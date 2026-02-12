from typing import Sequence
from uuid import UUID

from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only
from sqlalchemy_pydantic_mapper import ObjectMapper

from ..models import Group
from ..schemas import GroupSearchSchema


async def search_groups(
    user_id: UUID,
    name: str,
    limit: int,
    offset: int,
    session: AsyncSession,
) -> Sequence[GroupSearchSchema]:
    """
    Поиск групп по имени
    :param user_id: UUID пользователя вызывающего эндпоинт
    :param name: Строка для поиска по имени
    :param limit: лимит для поиска (максимальное число групп найденных за раз)
    :param offset: Смещение от "топа" похожих групп
    :param session: Сессия
    """

    await session.execute(select(func.set_config("pg_trgm.similarity_threshold", "0.1", True)))

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

    return await ObjectMapper.map_bulk(groups, GroupSearchSchema, user_id=user_id, session=session)
