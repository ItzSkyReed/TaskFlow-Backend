import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
)

from ..user.schemas import UserSchema
from .constants import LOGIN_PATTERN, PASSWORD_PATTERN


class SignUpSchema(BaseModel):
    login: Annotated[
        str,
        Field(
            ...,
            min_length=4,
            max_length=64,
            pattern=LOGIN_PATTERN,
            examples=["srun4ikPRO"],
            description="Login",
        ),
    ]
    email: Annotated[
        EmailStr,
        Field(
            ...,
            max_length=320,
            examples=["johndoe@example.com"],
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


class SignInSchema(BaseModel):
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
        try:
            TypeAdapter(EmailStr).validate_python(login_or_email)
            return login_or_email
        except ValidationError:
            pass

        if re.fullmatch(LOGIN_PATTERN, login_or_email):
            return login_or_email

        raise ValueError(
            "Identifier must be a valid email or login (letters, digits, underscore)"
        )


class ChangePasswordSchema(BaseModel):
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


class TokenSchema(BaseModel):
    access_token: Annotated[str, Field(...)]
    refresh_token: Annotated[str, Field(...)]


class TokenUserSchema(BaseModel):
    tokens: Annotated[TokenSchema, Field(...)]
    user: Annotated[UserSchema, Field(...)]


class RefreshTokenDataSchema(BaseModel):
    token: Annotated[str, Field(...)]
    jti: Annotated[UUID, Field(...)]


class TokenRefreshSchema(BaseModel):
    access_token: Annotated[str, Field(...)]
    refresh_token: Annotated[RefreshTokenDataSchema, Field(...)]


class TokenPayloadSchema(BaseModel):
    sub: Annotated[UUID, Field(...)]
    iat: Annotated[datetime, Field(...)]
    exp: Annotated[datetime, Field(...)]
    jti: Annotated[UUID | None, Field(default=None)]


class AccessTokenSchema(BaseModel):
    access_token: Annotated[str, Field(...)]
    token_type: Annotated[str, Field(default="bearer")] = "bearer"
