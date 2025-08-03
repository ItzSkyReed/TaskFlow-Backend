from datetime import UTC, datetime, timedelta
from logging import getLogger
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from starlette.requests import Request

from .config import get_auth_settings
from .exceptions import (
    AccessTokenNotFound,
    InvalidTokenException,
    TokenExpiredException,
)
from .schemas import (
    RefreshTokenDataSchema,
    TokenPayloadSchema,
    TokenRefreshSchema,
)

logger = getLogger(__name__)


class PasswordUtils:
    __password_hasher = PasswordHasher()

    @classmethod
    def hash_password(cls, password: str) -> str:
        return cls.__password_hasher.hash(password)

    @classmethod
    def verify_password(cls, hashed_password: str, password: str) -> bool:
        try:
            return cls.__password_hasher.verify(hash=hashed_password, password=password)
        except VerifyMismatchError:
            return False
        except (VerificationError, InvalidHashError) as e:
            logger.error(e)
            return False


class JWTUtils:
    __auth_settings = get_auth_settings()

    @classmethod
    def create_access_token(cls, user_id: str | UUID) -> str:
        now = datetime.now(UTC)

        payload = {
            "iat": now,
            "sub": str(user_id),
            "exp": now + timedelta(minutes=cls.__auth_settings.access_token_expires_in),
        }

        return jwt.encode(
            claims=payload,
            key=cls.__auth_settings.jwt_secret,
            algorithm=cls.__auth_settings.jwt_algorithm,
        )

    @classmethod
    def create_refresh_token(cls, user_id: str | UUID) -> RefreshTokenDataSchema:
        jti = uuid4()
        now = datetime.now(UTC)

        payload = {
            "iat": now,
            "sub": str(user_id),
            "exp": now
            + timedelta(minutes=cls.__auth_settings.refresh_token_expires_in),
            "jti": str(jti),
        }

        return RefreshTokenDataSchema(
            token=jwt.encode(
                claims=payload,
                key=cls.__auth_settings.jwt_secret,
                algorithm=cls.__auth_settings.jwt_algorithm,
            ),
            jti=jti,
        )

    @classmethod
    def decode_token(cls, token: str) -> TokenPayloadSchema:
        try:
            payload = jwt.decode(
                token,
                key=cls.__auth_settings.jwt_secret,
                algorithms=cls.__auth_settings.jwt_algorithm,
            )
            return TokenPayloadSchema.model_validate(payload)
        except ExpiredSignatureError as err:
            raise TokenExpiredException() from err
        except JWTError as err:
            raise InvalidTokenException() from err

    @classmethod
    def refresh_tokens(cls, user_id: UUID) -> TokenRefreshSchema:
        access_token = cls.create_access_token(user_id)
        refresh_token = cls.create_refresh_token(user_id)

        return TokenRefreshSchema(
            access_token=access_token, refresh_token=refresh_token
        )


class CustomHTTPBearer(HTTPBearer):
    def __init__(self):
        super().__init__(
            auto_error=False,
            bearerFormat="JWT",
            scheme_name="AccessToken",
            description="JWT access token encoded using HS256",
        )

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials = await super().__call__(request)
        if not credentials:
            raise AccessTokenNotFound()
        return credentials
