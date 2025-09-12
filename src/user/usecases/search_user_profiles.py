from logging import getLogger

from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, load_only

from ...user import User, UserProfile
from ..schemas import UserSearchSchema

logger = getLogger(__name__)


async def search_user_profiles(
    login: str,
    limit: int,
    offset: int,
    session: AsyncSession,
) -> list[UserSearchSchema]:
    """
    Поиск пользователей по login
    :param login: Строка для поиска по login
    :param limit: лимит для поиска (макс. число пользователей найденных за раз)
    :param offset: Смещение от "топа" похожих пользователей
    :param session: Сессия
    """

    await session.execute(select(func.set_config("pg_trgm.similarity_threshold", "0.1", True)))

    similarity_score = func.similarity(User.login, login)

    ilike_priority = case(
        (User.login.ilike(f"{login}%"), 2),
        (User.login.ilike(f"%{login}%"), 0),
        else_=1,
    )

    query = (
        select(User)
        .join(User.user_profile)
        .options(
            load_only(User.id, User.login, User.has_avatar),
            contains_eager(User.user_profile).load_only(UserProfile.name),
        )
        .where(
            or_(
                User.login.op("%")(login),
                User.login.ilike(f"{login}%"),
                User.login.ilike(f"%{login}%"),
            )
        )
        .order_by(desc(ilike_priority), desc(similarity_score))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(query)
    users_with_scores = result.scalars().all()

    return [UserSearchSchema.model_validate(user, from_attributes=True) for user in users_with_scores]
