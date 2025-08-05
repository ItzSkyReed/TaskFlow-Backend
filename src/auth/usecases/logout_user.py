from logging import getLogger

from ..exceptions import RefreshTokenNotWhitelisted
from ..services import (
    is_refresh_jti_valid,
    remove_refresh_token,
)
from ..utils import JWTUtils

logger = getLogger(__name__)


async def logout_user(
    refresh_token: str,
) -> None:
    """
    Логика выхода пользователя с сайта (удаление refresh токена из списка разрешенных)
    :param refresh_token: Refresh токен
    :raises RefreshTokenNotWhitelisted: Если refresh токен уже не в списке разрешенных
    """
    refresh_token_payload = JWTUtils.decode_token(refresh_token)

    if not is_refresh_jti_valid(refresh_token_payload.sub, refresh_token_payload.jti):
        raise RefreshTokenNotWhitelisted()

    await remove_refresh_token(refresh_token_payload.sub, refresh_token_payload.jti)
