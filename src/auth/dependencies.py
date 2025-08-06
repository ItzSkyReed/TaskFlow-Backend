from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..user import check_email_unique, check_login_unique
from .schemas import SignUpSchema


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
