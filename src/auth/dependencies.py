from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from src.auth.schemas import TokenPayloadSchema

from ..auth.schemas import SignUpSchema
from ..database import get_async_session
from ..user import User
from .exceptions import EmailAlreadyInUseException, LoginAlreadyInUseException
from .utils import CustomHTTPBearer, JWTUtils

custom_http_bearer = CustomHTTPBearer()


async def user_exists_by_field(
    session: AsyncSession, field: InstrumentedAttribute, value: str
) -> bool:
    result = await session.execute(select(User).where(field == value))
    return result.scalar_one_or_none() is not None


async def check_email_unique(user_in: SignUpSchema, session: AsyncSession):
    if await user_exists_by_field(session, User.email, user_in.email):
        raise EmailAlreadyInUseException()
    return user_in


async def check_login_unique(
    user_in: SignUpSchema, session: AsyncSession
) -> SignUpSchema:
    if await user_exists_by_field(session, User.login, user_in.login):
        raise LoginAlreadyInUseException()
    return user_in


async def validate_user_uniqueness(
    user_in: SignUpSchema,
    session: AsyncSession = Depends(get_async_session),
) -> SignUpSchema:
    await check_email_unique(user_in, session)
    await check_login_unique(user_in, session)
    return user_in


async def token_verification(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(custom_http_bearer)],
) -> TokenPayloadSchema:
    token = credentials.credentials
    payload = JWTUtils.decode_token(token)
    return payload
