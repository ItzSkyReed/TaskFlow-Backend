
from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from ..database import get_async_session
from ..user import User
from .exceptions import EmailAlreadyInUseException, LoginAlreadyInUseException
from .schemas import SignUpSchema


async def user_exists_by_field(
    field: InstrumentedAttribute,
    value: str,
    session: AsyncSession,
) -> bool:
    """
    Проверяет, существует ли уже пользователь с совпадающем значением в определенным полем
    :param session: Сессия
    :param field: Поле модели
    :param value: Значение поля
    """
    result = await session.execute(select(User).where(field == value))
    return result.scalar_one_or_none() is not None


async def check_email_unique(email: EmailStr, session: AsyncSession) -> None:
    """
    Проверяет уникален ли Email.
    :param email: Email пользователя
    :param session: Сессия
    :raises LoginAlreadyInUseException: Если такой email уже используется
    """
    if await user_exists_by_field(User.email, email, session):
        raise EmailAlreadyInUseException()


async def check_login_unique(login: str, session: AsyncSession) -> None:
    """
    Проверяет уникален ли Login.
    :param login: Login пользователя
    :param session: Сессия
    :raises LoginAlreadyInUseException: Если такой login уже используется
    """
    if await user_exists_by_field(User.login, login, session):
        raise LoginAlreadyInUseException()


async def validate_user_uniqueness(
    user_in: SignUpSchema,
    session: AsyncSession = Depends(get_async_session),
) -> SignUpSchema:
    """
    Проверяет уникален ли Email и Login пользователя.
    :param user_in: Схема регистрации пользователя
    :param session: Сессия
    """
    await check_email_unique(user_in.email, session)
    await check_login_unique(user_in.login, session)
    return user_in
