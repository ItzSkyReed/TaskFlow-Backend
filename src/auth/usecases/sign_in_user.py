from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import InvalidPasswordException
from ..schemas import SignInSchema, TokenSchema
from ..services import add_new_refresh_token, get_user_by_identifier
from ..utils import JWTUtils, PasswordUtils


async def sign_in_user(
    user_in: SignInSchema,
    session: AsyncSession,
) -> TokenSchema:
    """
    Логика входа пользователя на сайт
    :param user_in: Схема данных для входа
    :param session: Сессия
    :return: Схема содержащая access и refresh токены
    :raises InvalidPasswordException: Если пароль неверен
    """
    user = await get_user_by_identifier(user_in.identifier, session)

    if not PasswordUtils.verify_password(user.hashed_password, user_in.password):
        raise InvalidPasswordException()

    access_token = JWTUtils.create_access_token(user.id)
    refresh_token = JWTUtils.create_refresh_token(user.id)

    await add_new_refresh_token(user_id=user.id, token_jti=refresh_token.jti)

    return TokenSchema(access_token=access_token, refresh_token=refresh_token.token)
