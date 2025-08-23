from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..auth.schemas import TokenPayloadSchema
from ..auth.security import token_verification
from ..database import get_async_session
from ..schemas import ErrorResponseModel, UploadFileSchema
from .schemas import (
    CreateGroupSchema,
    GroupDetailSchema,
    GroupSummarySchema,
    InvitationSummarySchema,
    InviteUserToGroupSchema,
)
from .usecases import (
    create_group,
    delete_group_avatar,
    get_group,
    invite_user_to_group,
    patch_group_avatar,
    search_groups,
)

group_router = APIRouter(prefix="/group", tags=["Group"])


@group_router.get(
    "/search",
    name="Поиск групп по имени",
    status_code=status.HTTP_200_OK,
    response_model=list[GroupSummarySchema],  # список публичных групп (summary)
    description="Возвращает список групп, чьи имена максимально похожи на введенный текст",
    responses={
        200: {
            "description": "Успешный поиск групп",
            "model": list[GroupSummarySchema],
        },
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
    ],
)
async def search_groups_route(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    name: Annotated[
        str,
        Query(
            max_length=50,
            min_length=1,
            description="Строка подразумевающее возможное название группы",
        ),
    ],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Максимальное количество результатов")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Смещение от начала выборки")] = 0,
) -> list[GroupSummarySchema]:
    return await search_groups(name=name, limit=limit, offset=offset, session=session)


@group_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Создание группы пользователем",
    response_model=GroupDetailSchema,
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
) -> GroupDetailSchema:
    return await create_group(created_group, token_payload.sub, session)


@group_router.patch(
    "/{group_id}/avatar",
    status_code=status.HTTP_200_OK,
    name="Обновление аватарки группы",
    response_model=GroupDetailSchema,
    description="Позволяет владельцу группы или пользователям с правами обновить аватарку группы",
    responses={
        200: {"description": "Аватарка успешно изменена", "model": GroupDetailSchema},
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
) -> GroupDetailSchema:
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


@group_router.post(
    "/{group_id}/invitations",
    status_code=status.HTTP_201_CREATED,
    name="Приглашение пользователя в группу",
    response_model=InvitationSchema,
    description="Позволяет владельцу группы или пользователям с правами пригласить человека в группу, если такое приглашение уже существовало, вернется ранее сделанное",
    responses={
        201: {
            "description": "Приглашение пользователя в группу (новое или старое)",
            "model": InvitationSchema,
        },
        400: {
            "description": "Некорректный запрос",
            "model": ErrorResponseModel,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        403: {
            "description": "Недостаточно прав для приглашения пользователя в группу",
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
async def invite_user_to_group_route(
    group_id: Annotated[UUID, Path(...)],
    user_id: Annotated[InviteUserToGroupSchema, Body(...)],
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> InvitationSummarySchema:
    return await invite_user_to_group(
        group_id=group_id,
        inviter_id=token_payload.sub,
        invitee_id=user_id.user_id,
        session=session,
    )


@group_router.get(
    "/{group_id}",
    status_code=status.HTTP_200_OK,
    name="Получение информации о группе по ID",
    response_model=GroupDetailSchema,
    description="Создает группу, в которой пользователь будет являться владельцем",
    responses={
        200: {"description": "Группа успешно найдена", "model": None},
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        404: {"description": "Группы не существует", "model": ErrorResponseModel},
        422: {
            "description": "Некорректные данные в запросе (валидация схемы).",
            "model": ErrorResponseModel,
        },
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[Depends(token_verification)],
)
async def get_group_route(
    group_id: Annotated[UUID, Path(...)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> GroupDetailSchema:
    return await get_group(group_id, session)
