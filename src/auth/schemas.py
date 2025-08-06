from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
)

from ..user.constants import NAME_PATTERN
from .constants import LOGIN_PATTERN, PASSWORD_PATTERN


class TokenSchema(BaseModel):
    access_token: Annotated[str, Field(...)]
    refresh_token: Annotated[str, Field(...)]


class RefreshTokenDataSchema(BaseModel):
    token: Annotated[str, Field(...)]
    jti: Annotated[UUID, Field(...)]


class TokenRefreshSchema(BaseModel):
    access_token: Annotated[str, Field(...)]
    refresh_token: Annotated[RefreshTokenDataSchema, Field(...)]


class AccessTokenSchema(BaseModel):
    access_token: Annotated[str, Field(...)]
    token_type: Annotated[str, Field(default="bearer")] = "bearer"


class TokenPayloadSchema(BaseModel):
    """
    Поля Access/Refresh токена. JTI существует только у Refresh токена
    """

    sub: Annotated[UUID, Field(...)]
    iat: Annotated[datetime, Field(...)]
    exp: Annotated[datetime, Field(...)]
    jti: Annotated[UUID | None, Field(default=None)]


LoginStr = Annotated[str, StringConstraints(pattern=LOGIN_PATTERN)]


class SignUpSchema(BaseModel):
    """
    Схема регистрации пользователя
    """

    name: Annotated[
        str | None,
        Field(
            default=None,
            min_length=4,
            max_length=32,
            pattern=NAME_PATTERN,
            examples=["Joe_Sardina", "Margaret' Kabina", "x-MarinaPro228"],
            description="Публичное имя (при отсутствии будет совпадать с login)",
        ),
    ]
    login: Annotated[
        str,
        Field(
            ...,
            min_length=4,
            max_length=64,
            pattern=LOGIN_PATTERN,
            examples=["SuperUniqueLogin", "Login12345", "Login_megalogin"],
            description="Login",
        ),
    ]
    email: Annotated[
        EmailStr,
        Field(
            ...,
            examples=["johndoe@example.com", "nepoka@mail.ru"],
            description="Email адрес",
        ),
    ]
    password: Annotated[
        str,
        Field(
            ...,
            min_length=8,
            max_length=128,
            description="Пароль",
            pattern=PASSWORD_PATTERN,
        ),
    ]  # raw password
    model_config = ConfigDict(str_strip_whitespace=True)


class SignInSchema(BaseModel):
    """
    Схема входа пользователя
    """

    identifier: Annotated[
        str,
        Field(
            ...,
            max_length=320,
            description="Email или Login пользователя",
            examples=["johndoe@example.com", "srun4ikPRO"],
        ),
    ]
    password: Annotated[str, Field(..., min_length=8, max_length=128)]

    @classmethod
    @field_validator("identifier", mode="after")
    def validate_identifier(cls, login_or_email: str) -> str:
        """
        Проверка валидности идентификатора (должен соответствовать либо правилам Email, либо Login
        :param login_or_email: Login или Email пользователя
        :raises ValueError: Если login_or_email не проходит обе проверки валидации
        """
        try:
            EmailStr.validate(login_or_email)
            return login_or_email
        except ValidationError:
            pass

        try:
            # noinspection PyUnresolvedReferences
            LoginStr.validate(login_or_email)
            return login_or_email
        except ValidationError:
            pass

        raise ValueError(
            "Identifier must be a valid email or login (letters, digits, underscore)"
        )


class ChangePasswordSchema(BaseModel):
    """
    Схема смены пароля пользователя
    """

    old_password: Annotated[
        str,
        Field(
            ...,
            min_length=8,
            max_length=128,
            description="Старый пароль",
            pattern=PASSWORD_PATTERN,
        ),
    ]
    new_password: Annotated[
        str,
        Field(
            ...,
            min_length=8,
            max_length=128,
            description="Новый пароль",
            pattern=PASSWORD_PATTERN,
        ),
    ]
