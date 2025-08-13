# global configs
from functools import lru_cache
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    project_name: str = "Template"
    version: str = "0.0.1"
    cors_allowed_origins: List[str] = []
    environment: Literal["DEV", "PROD"] = Field(
        "DEV", description="App environment: DEV or PROD"
    )
    root_path: str
    api_prefix: str
    cdn_path: str

    debug: bool = False
    db_echo: bool = False
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_out_host: str
    postgres_port: int
    postgres_out_port: int

    redis_user: str
    redis_password: str
    redis_host: str
    redis_port: int
    redis_out_port: int

    minio_root_user: str
    minio_root_password: str
    minio_web_port: int
    minio_out_web_port: int
    minio_storage_port: int
    minio_out_storage_port: int

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def outside_docker_database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_out_host,
            port=self.postgres_out_port,
            database=self.postgres_db,
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# noinspection PyArgumentList
@lru_cache
def get_settings() -> Settings:
    return Settings()  # ty: ignore[missing-argument]
