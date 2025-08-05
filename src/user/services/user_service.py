from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ...user import User, UserNotFoundByIdentifierException, UserNotFoundByIdException


async def get_user_by_identifier(identifier: str, session: AsyncSession) -> User:
    """
    Получение пользователя по identifier
    :param identifier: Login/Email пользователя
    :param session: Сессия
    :raises UserNotFoundByIdentifierException: Если пользователь не найден
    """
    user = (
        await session.execute(
            select(User).where(or_(User.email == identifier, User.login == identifier))
        )
    ).scalar_one_or_none()
    if not user:
        raise UserNotFoundByIdentifierException()
    return user


async def get_user_by_id(user_id: UUID, session: AsyncSession) -> User:
    """
    Получение пользователя по identifier
    :param user_id: UUID пользователя
    :param session: Сессия
    :raises UserNotFoundByIdException: Если пользователь не найден
    """
    user = (
        await session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if user is None:
        raise UserNotFoundByIdException()
    return user


async def get_user_with_profile(user_id: UUID, session: AsyncSession) -> User | None:
    """
    Получение пользователя с загруженным UserProfile
    :param user_id: Id пользователя
    :param session: Сессия
    :raises UserNotFoundByIdException: Если пользователь не найден
    """
    user = (
        await session.execute(
            select(User)
            .options(joinedload(User.user_profile))
            .filter(User.id == user_id)
        )
    ).scalar_one_or_none()
    if user is None:
        raise UserNotFoundByIdException()
    return user
