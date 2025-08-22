from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Path
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..auth.schemas import TokenPayloadSchema
from ..auth.security import token_verification
from ..database import get_async_session
from ..schemas import ErrorResponseModel, UploadFileSchema
from .schemas import CreateGroupSchema, GroupSchema
from .usecases import create_group, delete_group_avatar, patch_group_avatar

group_router = APIRouter(prefix="/group", tags=["Group"])


@group_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Создание группы пользователем",
    response_model=GroupSchema,
    description="Создает группу, в которой пользователь будет являться владельцем",
    responses={
        204: {"description": "Аватарка успешно удалена", "model": None},
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        403: {
            "description": "Превышено количество возможных созданных пользователем групп",
            "model": ErrorResponseModel,
        },
        404: {
            "description": "Пользователь не найден",
            "model": ErrorResponseModel,
        },
        422: {
            "description": "Некорректные данные в запросе (валидация схемы).",
            "model": ErrorResponseModel,
        },
        429: {"description": "Превышены лимиты API.", "model": ErrorResponseModel},
        500: {"description": "Внутренняя ошибка сервера."},
    },
)
async def create_group_route(
    created_group: Annotated[
        CreateGroupSchema,
        Body(
            ...,
        ),
    ],
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> GroupSchema:
    return await create_group(created_group, token_payload.sub, session)


@group_router.patch(
    "/{group_id}/avatar",
    status_code=status.HTTP_200_OK,
    name="Обновление аватарки группы",
    response_model=GroupSchema,
    description="Позволяет владельцу группы или пользователям с правами обновить аватарку группы",
    responses={
        200: {"description": "Аватарка успешно изменена", "model": GroupSchema},
        400: {
            "description": "Некорректный формат файла, или сам файл не фото",
            "model": ErrorResponseModel,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        403: {
            "description": "Недостаточно прав для изменения аватара группы",
            "model": ErrorResponseModel,
        },
        404: {
            "description": "Группы с таким ID не существует",
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
)
async def patch_group_avatar_route(
    group_id: Annotated[UUID, Path(...)],
    file: Annotated[
        UploadFileSchema, File(..., description="Файл аватарки в формате webp")
    ],
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> GroupSchema:
    return await patch_group_avatar(
        file=file.file,
        group_id=group_id,
        initiator_id=token_payload.sub,
        session=session,
    )


@group_router.delete(
    "/{group_id}/avatar",
    status_code=status.HTTP_204_NO_CONTENT,
    name="Удаление аватарки группы",
    response_model=None,
    description="Позволяет владельцу группы или пользователям с правами удалить аватарку группы",
    responses={
        204: {"description": "Аватарка успешно удалена", "model": None},
        400: {
            "description": "Некорректный запрос",
            "model": ErrorResponseModel,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        403: {
            "description": "Недостаточно прав для изменения аватара группы",
            "model": ErrorResponseModel,
        },
        404: {
            "description": "Группы с таким ID не существует",
            "model": ErrorResponseModel,
        },
        422: {
            "description": "Некорректные данные в запросе (валидация схемы).",
            "model": ErrorResponseModel,
        },
        429: {"description": "Превышены лимиты API.", "model": ErrorResponseModel},
        500: {"description": "Внутренняя ошибка сервера."},
    },
)
async def delete_group_avatar_route(
    group_id: Annotated[UUID, Path(...)],
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    await delete_group_avatar(
        group_id=group_id,
        initiator_id=token_payload.sub,
        session=session,
    )
    return None
