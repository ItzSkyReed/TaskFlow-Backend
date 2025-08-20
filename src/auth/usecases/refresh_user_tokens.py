from ..exceptions import RefreshTokenNotWhitelisted
from ..schemas import TokenSchema
from ..services import (
    add_new_refresh_token,
    is_refresh_jti_valid,
    remove_refresh_token,
)
from ..utils import JWTUtils


async def refresh_user_tokens(
    refresh_token: str,
) -> TokenSchema:
    """
    Логика обновления токенов пользователя
    :param refresh_token: refresh токен пользователя
    :return: Схема содержащая access и refresh токены
    :raises RefreshTokenNotWhitelisted: Если refresh токен не в списке разрешенных
    """
    refresh_token_payload = JWTUtils.decode_token(refresh_token)

    if not await is_refresh_jti_valid(
        refresh_token_payload.sub,
        refresh_token_payload.jti,  # ty: ignore[invalid-argument-type]
    ):
        raise RefreshTokenNotWhitelisted()

    new_tokens = JWTUtils.refresh_tokens(refresh_token_payload.sub)

    await remove_refresh_token(
        user_id=refresh_token_payload.sub,
        token_jti=refresh_token_payload.jti,  # type: ignore[arg-type]
    )
    await add_new_refresh_token(refresh_token_payload.sub, new_tokens.refresh_token.jti)
    return TokenSchema(
        access_token=new_tokens.access_token,
        refresh_token=new_tokens.refresh_token.token,
    )
