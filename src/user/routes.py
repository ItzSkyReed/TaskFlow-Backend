from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..auth.schemas import TokenPayloadSchema
from ..auth.security import token_verification
from ..database import get_async_session
from .schemas import PublicUserSchema, UserSchema
from .usecases import get_my_profile, get_public_user_profile

profile_router = APIRouter(prefix="/profile", tags=["Profile"])


@profile_router.get(
    "/me",
    name="Получение полной информации о своем профиле",
    status_code=status.HTTP_200_OK,
    response_model=UserSchema,
    description="Видны все поля",
    responses={
        200: {"description": "Успешное получение профиля"},
        400: {"description": "Некорректные данные в запросе."},
        401: {"description": "Access token не найден, истек или некорректен"},
        422: {"description": "Некорректные данные в запросе (валидация схемы)."},
        429: {"description": "Превышены лимиты API."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[
        Depends(RateLimiter(times=100, seconds=30)),
    ],
)
async def get_my_profile_route(
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserSchema:
    return await get_my_profile(token_payload.sub, session)


@profile_router.get(
    "/{uuid: UUID}",
    name="Получение публичного профиля пользователя",
    status_code=status.HTTP_200_OK,
    response_model=PublicUserSchema,
    description="Видны только публичные поля",
    responses={
        200: {"description": "Успешное получение профиля"},
        400: {"description": "Некорректные данные в запросе."},
        401: {"description": "Access token не найден, истек или некорректен"},
        422: {"description": "Некорректные данные в запросе (валидация схемы)."},
        429: {"description": "Превышены лимиты API."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[
        Depends(token_verification),
        Depends(RateLimiter(times=100, seconds=30)),
    ],
)
async def get_public_user_profile_route(
    uuid: Annotated[UUID, Path(description="UUID пользователя")],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> PublicUserSchema:
    return await get_public_user_profile(uuid, session)
