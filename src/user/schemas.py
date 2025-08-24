from datetime import datetime
from typing import Annotated, Optional, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    model_validator,
)
from ..config import get_settings
from ..constants import USER_NAME_PATTERN, USER_LOGIN_PATTERN
settings = get_settings()

class UserAvatarMixin(BaseModel):

    has_avatar: Annotated[bool, Field(default=False, exclude=True)]

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        if getattr(self, "has_avatar", False):
            return f"{settings.cdn_path}/avatars/users/{self.id}.webp"
        return None

class UserSchema(UserAvatarMixin, BaseModel):
    """
    Модель пользователя с профилем

    """

    id: UUID

    login: Annotated[
        str, Field(..., min_length=4, max_length=64, pattern=USER_LOGIN_PATTERN)
    ]

    email: Annotated[EmailStr, Field(..., max_length=320)]

    registered_at: Annotated[datetime, Field(..., validation_alias="created_at")]

    profile: Annotated["ProfileSchema", Field(..., validation_alias="user_profile")]

    model_config = ConfigDict(from_attributes=True)


class ProfileSchema(BaseModel):
    name: Annotated[str, Field(max_length=32)]
    discord_username: Annotated[str | None, Field(default=None, max_length=32)]
    telegram_username: Annotated[str | None, Field(default=None, max_length=32)]

    show_discord: Annotated[bool, Field(...)]
    show_telegram: Annotated[bool, Field(...)]
    show_email: Annotated[bool, Field(...)]


class PublicUserSchema(UserAvatarMixin, BaseModel):
    id: UUID

    login: Annotated[
        str, Field(..., min_length=4, max_length=64, pattern=USER_LOGIN_PATTERN)
    ]

    email: Annotated[EmailStr | None, Field(default=None, max_length=320)]

    registered_at: Annotated[datetime, Field(..., validation_alias="created_at")]

    profile: Annotated[
        "PublicProfileSchema", Field(..., validation_alias="user_profile")
    ]

    @model_validator(mode="after")
    def check_profile_visibility(self):
        if not self.profile.show_email:
            self.email = None
        return self

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

    @model_validator(mode="after")
    def check_visibility_and_fields(self):
        if not self.show_telegram:
            self.telegram_username = None

        if not self.show_discord:
            self.discord_username = None

        return self

    model_config = ConfigDict(from_attributes=True)


class PatchUserSchema(BaseModel):
    email: Annotated[
        EmailStr | None,
        Field(
            default=None,
            examples=["johndoe@example.com", "nepoka@mail.ru"],
            description="Email адрес",
        ),
    ]

    profile: Annotated[
        Optional["PatchProfileSchema"],
        Field(default=None, serialization_alias="user_profile"),
    ]

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        # noinspection PyTypeChecker
        if not any(
            getattr(self, field) is not None for field in self.__class__.model_fields
        ):
            raise ValueError("Должно быть указано хотя бы одно поле для обновления.")
        return self


class PatchProfileSchema(BaseModel):
    name: Annotated[
        str | None,
        Field(
            default=None,
            min_length=4,
            max_length=32,
            pattern=USER_NAME_PATTERN,
            examples=["Joe_Sardina", "Margaret' Kabina", "x-MarinaPro228"],
            description="Публичное имя",
        ),
    ]
    show_discord: Annotated[
        bool | None,
        Field(
            default=None,
            description="Показывать ли остальным пользователям discord username",
        ),
    ]
    show_telegram: Annotated[
        bool | None,
        Field(
            default=None,
            description="Показывать ли остальным пользователям telegram username",
        ),
    ]
    show_email: Annotated[
        bool | None,
        Field(default=None, description="Показывать ли остальным пользователям email"),
    ]

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        # noinspection PyTypeChecker
        if not any(
            getattr(self, field) is not None for field in self.__class__.model_fields
        ):
            raise ValueError("Должно быть указано хотя бы одно поле для обновления.")
        return self

class UserSearchSchema(UserAvatarMixin, BaseModel):
    """
    Модель пользователя с профилем

    """

    id: UUID

    login: Annotated[
        str, Field(..., min_length=4, max_length=64, pattern=USER_LOGIN_PATTERN)
    ]

    profile: Annotated["UserSearchProfileSchema", Field(..., validation_alias="user_profile")]

    model_config = ConfigDict(from_attributes=True)

class UserSearchProfileSchema(BaseModel):
    name: Annotated[str, Field(max_length=32)]

    model_config = ConfigDict(from_attributes=True)