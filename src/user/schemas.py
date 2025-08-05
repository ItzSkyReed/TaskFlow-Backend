from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from ..auth.constants import LOGIN_PATTERN


class UserSchema(BaseModel):
    """
    Модель пользователя с профилем

    """

    id: UUID
    login: Annotated[
        str, Field(..., min_length=4, max_length=64, pattern=LOGIN_PATTERN)
    ]
    email: Annotated[EmailStr, Field(..., max_length=320)]

    registered_at: Annotated[datetime, Field(..., alias="created_at")]

    profile: Annotated["ProfileSchema", Field(..., alias="user_profile")]

    model_config = ConfigDict(from_attributes=True)


class ProfileSchema(BaseModel):
    name: Annotated[str, Field(max_length=32)]
    discord_username: Annotated[str | None, Field(default=None, max_length=32)]
    telegram_username: Annotated[str | None, Field(default=None, max_length=32)]

    show_discord: Annotated[bool, Field(...)]
    show_telegram: Annotated[bool, Field(...)]
    show_email: Annotated[bool, Field(...)]


class PublicUserSchema(BaseModel):
    id: UUID

    email: Annotated[EmailStr, Field(default=None, max_length=320)]

    registered_at: Annotated[datetime, Field(..., alias="created_at")]

    profile: Annotated["PublicProfileSchema", Field(..., alias="user_profile")]

    @classmethod
    @model_validator(mode="after")
    def check_profile_visibility(cls, values):
        if not values.profile.show_email:
            values.email = None
        return values

    model_config = ConfigDict(from_attributes=True)


class PublicProfileSchema(BaseModel):
    name: Annotated[str, Field(..., max_length=32)]
    telegram_username: Annotated[
        str | None, Field(default=None, min_length=4, max_length=64)
    ]
    discord_username: Annotated[
        str | None, Field(default=None, min_length=4, max_length=64)
    ]

    show_telegram: Annotated[bool, Field(default=False, exclude=True)]
    show_discord: Annotated[bool, Field(default=False, exclude=True)]
    show_email: Annotated[bool, Field(default=False, exclude=True)]

    @classmethod
    @model_validator(mode="after")
    def check_visibility_and_fields(cls, values):
        if not values.show_telegram:
            values.telegram_username = None

        if not values.show_discord:
            values.discord_username = None

        return values

    model_config = ConfigDict(from_attributes=True)
