from logging import getLogger

from sqlalchemy.ext.asyncio import AsyncSession

from ...user.services import get_user_by_id
from ..exceptions import (
    InvalidOldPasswordException,
    PasswordsAreSameException,
    RefreshTokenNotWhitelisted,
)
from ..schemas import ChangePasswordSchema
from ..services import (
    is_refresh_jti_valid,
    remove_all_refresh_tokens_except,
)
from ..utils import JWTUtils, PasswordUtils

logger = getLogger(__name__)


async def change_user_password(
    passwords: ChangePasswordSchema,
    refresh_token: str,
    session: AsyncSession,
):
    """
    Логика изменения пароля пользователя
    :param passwords: Схема с паролями пользователей
    :param refresh_token: Refresh token пользователя
    :param session: Сессия
    :raises RefreshTokenNotWhitelisted: Если Refresh токена нет в redis (разрешенные токены)
    :raises InvalidOldPasswordException: Если старый пароль не совпадает с актуальным
    :raises PasswordsAreSameException: Если старый и новый пароль одинаковы
    """

    if passwords.old_password == passwords.new_password:
        raise PasswordsAreSameException()

    refresh_token_payload = JWTUtils.decode_token(refresh_token)

    if not is_refresh_jti_valid(refresh_token_payload.sub, refresh_token_payload.jti):  # type: ignore[arg-type]
        raise RefreshTokenNotWhitelisted()

    user = await get_user_by_id(refresh_token_payload.sub, session)

    # noinspection PyTypeChecker
    if not PasswordUtils.verify_password(user.hashed_password, passwords.old_password):
        raise InvalidOldPasswordException()

    new_hashed_password = PasswordUtils.hash_password(passwords.new_password)

    user.hashed_password = new_hashed_password
    await session.commit()

    await remove_all_refresh_tokens_except(
        user_id=refresh_token_payload.sub,
        except_token_jti=refresh_token_payload.jti,  # type: ignore[arg-type]
    )
