from sqlalchemy import desc, func, literal, select, case, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import User, UserProfile
from ..schemas import PublicUserSchema


async def search_user_profiles(
    name: str,
    limit: int,
    offset: int,
    session: AsyncSession,
) -> list[PublicUserSchema]:
    """
    Поиск пользователей по имени
    :param name: Строка для поиска по имени
    :param limit: лимит для поиска (макс. число пользователей найденных за раз)
    :param offset: Смещение от "топа" похожих пользователей
    :param session: Сессия
    """

    similarity_score = func.similarity(UserProfile.name, name)

    ilike_priority = case(
            (UserProfile.name.ilike(f"{name}%"), 2),
            (UserProfile.name.ilike(f"%{name}%"), 1),
        else_=0
    )

    query = (
        select(User, similarity_score.label("score"))
        .join(User.user_profile)
        .join(
            select(func.set_config("pg_trgm.similarity_threshold", "0.1", True)).cte(
                "set_threshold"
            ),
            literal(True, literal_execute=True),
        )
        .options(joinedload(User.user_profile))
        .where(
            or_(
                UserProfile.name.op("%")(name),
                UserProfile.name.ilike(f"{name}%"),
                UserProfile.name.ilike(f"%{name}%")
        ))
        .order_by(desc(ilike_priority), desc(similarity_score))
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(query)
    users_with_scores = result.all()

    return [
        PublicUserSchema.model_validate(user, from_attributes=True)
        for user, _ in users_with_scores
    ]
