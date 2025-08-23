from logging import getLogger

from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from .. import User, UserProfile
from ..schemas import PublicUserSchema

logger = getLogger(__name__)


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

    await session.execute(
        select(func.set_config("pg_trgm.similarity_threshold", "0.1", True))
    )

    similarity_score = func.similarity(UserProfile.name, name)

    ilike_priority = case(
        (UserProfile.name.ilike(f"{name}%"), 2),
        (UserProfile.name.ilike(f"%{name}%"), 0),
        else_=1,
    )

    query = (
        select(User, similarity_score.label("score"))
        .join(User.user_profile)
        .options(contains_eager(User.user_profile))
        .where(
            or_(
                UserProfile.name.op("%")(name),
                UserProfile.name.ilike(f"{name}%"),
                UserProfile.name.ilike(f"%{name}%"),
            )
        )
        .order_by(desc(ilike_priority), desc(similarity_score))
        .limit(limit)
        .offset(offset)
    )

    logger.info(
        query.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )

    result = await session.execute(query)
    users_with_scores = result.all()

    return [
        PublicUserSchema.model_validate(user, from_attributes=True)
        for user, _ in users_with_scores
    ]
