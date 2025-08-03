from functools import lru_cache
from logging import getLogger

from pydantic_settings import BaseSettings

logger = getLogger(__name__)


class AuthSettings(BaseSettings):
    access_token_expires_in: int  # minutes
    refresh_token_expires_in: int  # minutes

    jwt_algorithm: str
    jwt_secret: str

    class Config:
        env_prefix = "AUTH_"
        env_file = ".env"
        extra = "ignore"


# noinspection PyArgumentList
@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings()
