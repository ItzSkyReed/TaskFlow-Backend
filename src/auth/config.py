from functools import lru_cache
from logging import getLogger

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = getLogger(__name__)


class AuthSettings(BaseSettings):
    access_token_expires_in: int  # minutes
    refresh_token_expires_in: int  # minutes

    jwt_algorithm: str
    jwt_secret: str

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_prefix="AUTH_"
    )


# noinspection PyArgumentList
@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings()
