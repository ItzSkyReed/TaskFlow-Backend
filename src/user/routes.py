from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Path
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..auth.schemas import TokenPayloadSchema
from ..auth.security import token_verification
from ..database import get_async_session
from ..schemas import ErrorResponseModel, UploadFileSchema
from .schemas import PatchUserSchema, PublicUserSchema, UserSchema
from .usecases import (
    delete_my_profile_avatar,
    get_my_profile,
    get_public_user_profile,
    patch_my_profile,
    patch_my_profile_avatar,
)

profile_router = APIRouter(prefix="/profile", tags=["Profile"])


@profile_router.get(
    "/me",
    name="Получение полной информации о своем профиле",
    status_code=status.HTTP_200_OK,
    response_model=UserSchema,
    description="Видны все поля",
    responses={
        200: {"description": "Успешное получение профиля", "model": UserSchema},
        400: {
            "description": "Некорректные данные в запросе.",
            "model": ErrorResponseModel,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        422: {
            "description": "Некорректные данные в запросе (валидация схемы).",
            "model": ErrorResponseModel,
        },
        429: {"description": "Превышены лимиты API.", "model": ErrorResponseModel},
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


@profile_router.patch(
    "/me",
    name="Изменение информации о профиле",
    status_code=status.HTTP_200_OK,
    response_model=UserSchema,
    description="Возможно изменять не все поля, нельзя отправлять пустые запросы",
    responses={
        200: {"description": "Успешное изменение профиля", "model": UserSchema},
        400: {
            "description": "Некорректные данные в запросе.",
            "model": ErrorResponseModel,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        409: {
            "description": "Используется email который уже у кого-то указан",
            "model": ErrorResponseModel,
        },
        422: {
            "description": "Некорректные данные в запросе (валидация схемы).",
            "model": ErrorResponseModel,
        },
        429: {"description": "Превышены лимиты API.", "model": ErrorResponseModel},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[
        Depends(RateLimiter(times=50, minutes=1)),
    ],
)
async def patch_my_profile_route(
    patch_schema: Annotated[PatchUserSchema, Body(...)],
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserSchema:
    return await patch_my_profile(patch_schema, token_payload.sub, session)


@profile_router.delete(
    "/me/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    name="Удаление аватарки пользователя",
    response_model=None,
    description="Удаление аватарки пользователя безвозвратно",
    responses={
        204: {"description": "Аватарка успешно удалена", "model": None},
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        429: {"description": "Превышены лимиты API.", "model": ErrorResponseModel},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[Depends(RateLimiter(times=50, minutes=1))],
)
async def delete_my_avatar_route(
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    await delete_my_profile_avatar(token_payload.sub, session)
    return None


@profile_router.patch(
    "/me/avatar",
    status_code=status.HTTP_200_OK,
    name="Изменение аватарки пользователя",
    response_model=UserSchema,
    description="Загрузка аватарки, допустим только формат webp",
    responses={
        200: {"description": "Аватарка успешно загружена", "model": UserSchema},
        400: {
            "description": "Некорректный формат файла, должен быть webp",
            "model": ErrorResponseModel,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        413: {
            "description": "Аватар слишком большой (вес файла)",
            "model": ErrorResponseModel,
        },
        422: {
            "description": "Некорректные данные в запросе (валидация схемы).",
            "model": ErrorResponseModel,
        },
        429: {"description": "Превышены лимиты API.", "model": ErrorResponseModel},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[Depends(RateLimiter(times=20, minutes=1))],
)
async def patch_my_avatar_route(
    file: Annotated[
        UploadFileSchema, File(..., description="Файл аватарки в формате webp")
    ],
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> UserSchema:
    return await patch_my_profile_avatar(file.file, token_payload.sub, session)


@profile_router.get(
    "/{uuid}",
    name="Получение публичного профиля пользователя",
    status_code=status.HTTP_200_OK,
    response_model=PublicUserSchema,
    description="Видны только публичные поля",
    responses={
        200: {"description": "Успешное получение профиля", "model": PublicUserSchema},
        400: {
            "description": "Некорректные данные в запросе.",
            "model": ErrorResponseModel,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        422: {
            "description": "Некорректные данные в запросе (валидация схемы).",
            "model": ErrorResponseModel,
        },
        429: {"description": "Превышены лимиты API.", "model": ErrorResponseModel},
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
