from sqlalchemy import desc, func, literal, select, case, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Group
from ..schemas import GroupSummarySchema


async def search_groups(
        name: str,
        limit: int,
        offset: int,
        session: AsyncSession,
) -> list[GroupSummarySchema]:
    """
    Поиск групп по имени
    :param name: Строка для поиска по имени
    :param limit: лимит для поиска (макс. число групп найденных за раз)
    :param offset: Смещение от "топа" похожих групп
    :param session: Сессия
    """

    similarity_score = func.similarity(Group.name, name)

    ilike_priority = case(
        (Group.name.ilike(f"{name}%"), 2),  # начинается с name
        (Group.name.ilike(f"%{name}%"), 0),  # содержит name
        else_=1
    )

    query = (
        select(Group, similarity_score.label("score"))
        .join(
            select(func.set_config("pg_trgm.similarity_threshold", "0.1", True)).cte(
                "set_threshold"
            ),
            literal(True, literal_execute=True),
        )
        .where(
            or_(
                Group.name.op("%")(name),  # поиск через триграммы
                Group.name.ilike(f"{name}%"),  # начинается с
                Group.name.ilike(f"%{name}%")  # содержит
        ))
        .order_by(desc(ilike_priority), desc(similarity_score))
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(query)
    groups_with_scores = result.all()

    return [
        GroupSummarySchema.model_validate(group, from_attributes=True)
        for group, _ in groups_with_scores
    ]
