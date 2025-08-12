from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.requests import Request

from .exceptions import AccessTokenNotFound
from .utils import JWTUtils

if TYPE_CHECKING:  # To avoid circular imports
    from .schemas import TokenPayloadSchema


class CustomHTTPBearer(HTTPBearer):
    def __init__(self):
        super().__init__(
            auto_error=False,
            bearerFormat="JWT",
            scheme_name="AccessToken",
            description="JWT access token encoded using HS256",
        )

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        """
        :raises AccessTokenNotFound: Если access token не найден в запросе
        """
        credentials = await super().__call__(request)
        if not credentials:
            raise AccessTokenNotFound()
        return credentials


custom_http_bearer = CustomHTTPBearer()


async def token_verification(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(custom_http_bearer)],
) -> TokenPayloadSchema:
    """
    Верифицирует access токен
    :param credentials: Заголовок авторизации
    """
    token = credentials.credentials
    payload = JWTUtils.decode_token(token)
    return payload
