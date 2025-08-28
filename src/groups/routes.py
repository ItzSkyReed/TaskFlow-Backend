from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..auth.schemas import TokenPayloadSchema
from ..auth.security import token_verification
from ..database import get_async_session
from ..schemas import ErrorResponseModel, UploadFileSchema
from .enums import InvitationStatus
from .schemas import (
    CreateGroupSchema,
    GroupDetailSchema,
    GroupSearchSchema,
    GroupSummarySchema,
    InvitationSummarySchema,
    InviteUserToGroupSchema,
    PatchGroupSchema,
    GroupInvitationSchema, RespondToInvitationSchema,
)
from .usecases import (
    create_group,
    delete_group_avatar,
    delete_user_from_group,
    get_group,
    get_received_invitations,
    get_user_groups,
    invite_user_to_group,
    patch_group,
    patch_group_avatar,
    search_groups, respond_to_invitation,
)

group_router = APIRouter(prefix="/group", tags=["Group"])


@group_router.get(
    "/search",
    name="Поиск групп по имени",
    status_code=status.HTTP_200_OK,
    response_model=list[GroupSearchSchema],  # список публичных групп (summary)
    description="Возвращает список групп, чьи имена максимально похожи на введенный текст",
    responses={
        200: {
            "description": "Успешный поиск групп",
            "model": list[GroupSearchSchema],
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
)
async def search_groups_route(
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
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
) -> list[GroupSearchSchema]:
    return await search_groups(
        user_id=token_payload.sub,
        name=name,
        limit=limit,
        offset=offset,
        session=session,
    )


@group_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    name="Создание группы пользователем",
    response_model=GroupDetailSchema,
    description="Создает группу, в которой пользователь будет являться владельцем",
    responses={
        201: {"description": "Группа успешно создана", "model": GroupDetailSchema},
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        409: {
            "description": "Группа с таким названием уже создана",
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
    "/{group_id}",
    status_code=status.HTTP_200_OK,
    name="Обновление информации о группе",
    response_model=GroupDetailSchema,
    description="Позволяет владельцу группы или пользователям с правами обновить параметры группы",
    responses={
        200: {"description": "Группа успешно изменена", "model": GroupDetailSchema},
        400: {
            "description": "Некорректный формат cхемы",
            "model": ErrorResponseModel,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        403: {
            "description": "Недостаточно прав для изменения группы",
            "model": ErrorResponseModel,
        },
        404: {
            "description": "Группы с таким ID не существует",
            "model": ErrorResponseModel,
        },
        409: {
            "description": "Группа с таким названием уже существует/Предложенное макс. кол-во участником меньше, чем актуальное число участников в группе",
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
async def patch_group_route(
    group_id: Annotated[UUID, Path(...)],
    patch_schema: Annotated[PatchGroupSchema, Body(...)],
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> GroupDetailSchema:
    return await patch_group(
        patched_group=patch_schema,
        group_id=group_id,
        initiator_id=token_payload.sub,
        session=session,
    )


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
    response_model=InvitationSummarySchema,
    description="Позволяет владельцу группы или пользователям с правами пригласить человека в группу, если такое приглашение уже существовало, вернется ранее сделанное",
    responses={
        201: {
            "description": "Приглашение пользователя в группу (новое или старое)",
            "model": InvitationSummarySchema,
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
        200: {"description": "Группа успешно найдена", "model": GroupDetailSchema},
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
)
async def get_group_route(
    group_id: Annotated[UUID, Path(...)],
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> GroupDetailSchema:
    return await get_group(group_id, token_payload.sub, session)


@group_router.get(
    "/invitations/received",
    status_code=status.HTTP_200_OK,
    name="Получение списка групп, куда вы приглашены",
    response_model=list[GroupInvitationSchema],
    description="Создает группу, в которой пользователь будет являться владельцем",
    responses={
        200: {
            "description": "Группа успешно найдена",
            "model": list[GroupInvitationSchema],
        },
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
)
async def get_received_invitations_route(
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    invitation_status: Annotated[
        list[InvitationStatus] | None,
        Query(description="По каким статусам заявок фильтровать"),
    ] = None,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Максимальное количество результатов")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Смещение от начала выборки")] = 0,
) -> list[GroupInvitationSchema]:
    return await get_received_invitations(
        invitation_status=invitation_status,
        limit=limit,
        offset=offset,
        session=session,
        invitee_id=token_payload.sub,
    )

@group_router.patch(
    "/invitations/{invitation_id}",
    status_code=status.HTTP_200_OK,
    name="Отправка ответа на определенное приглашение в группу",
    response_model=GroupInvitationSchema,
    description="Создает группу, в которой пользователь будет являться владельцем",
    responses={
        200: {
            "description": "Приглашение успешно обработано (отклонено/принято)",
            "model": GroupInvitationSchema,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        404: {"description": "Приглашения не существует", "model": ErrorResponseModel},
        409: {"description": "Группа переполнена пользователями", "model": ErrorResponseModel},
        422: {
            "description": "Некорректные данные в запросе (валидация схемы).",
            "model": ErrorResponseModel,
        },
        500: {"description": "Внутренняя ошибка сервера."},
    },
)
async def respond_to_invitation_route(
        token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
        session: Annotated[AsyncSession, Depends(get_async_session)],
        invitation_id: Annotated[UUID, Path(...)],
        response: Annotated[RespondToInvitationSchema, Body(...),],
) -> GroupInvitationSchema:
    return await respond_to_invitation(
        respond_status=response,
        session=session,
        invitation_id=invitation_id,
        user_id=token_payload.sub,
    )

@group_router.get(
    "/mine/groups",
    name="Получение списка своих групп где состоит пользователь из access_token",
    status_code=status.HTTP_200_OK,
    response_model=list[GroupSummarySchema],
    description="Получение списка своих групп где состоит пользователь из access_token",
    responses={
        200: {
            "description": "Успешное получение профиля",
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
async def get_mine_groups_route(
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[GroupSummarySchema]:
    return await get_user_groups(token_payload.sub, session)


@group_router.get(
    "/{user_id}/groups",
    name="Получение списка групп в которых есть пользователь",
    status_code=status.HTTP_200_OK,
    response_model=list[GroupSummarySchema],
    description="Получение списка групп в которых есть пользователь c опред. ID",
    responses={
        200: {
            "description": "Успешное получение профиля",
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
    dependencies=[
        Depends(token_verification),
    ],
)
async def get_user_groups_route(
    user_id: Annotated[UUID, Path(description="UUID пользователя")],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[GroupSummarySchema]:
    return await get_user_groups(user_id, session)


@group_router.delete(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="Исключение пользователя из группы",
    response_model=None,
    description="Позволяет владельцу группы или пользователям с правами исключить пользователя из неё",
    responses={
        204: {"description": "Пользователь успешно исключен", "model": None},
        400: {
            "description": "Некорректный запрос",
            "model": ErrorResponseModel,
        },
        401: {
            "description": "Access token не найден, истек или некорректен",
            "model": ErrorResponseModel,
        },
        403: {
            "description": "Недостаточно прав для изменения исключения пользователя из группы; Невозможно исключить создателя группы",
            "model": ErrorResponseModel,
        },
        404: {
            "description": "Группы с таким ID не существует",
            "model": ErrorResponseModel,
        },
        409: {
            "description": "Невозможно исключить из группы себя",
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
async def delete_user_from_group_route(
    group_id: Annotated[UUID, Path(...)],
    user_id: Annotated[UUID, Path(...)],
    token_payload: Annotated[TokenPayloadSchema, Depends(token_verification)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    await delete_user_from_group(
        group_id=group_id,
        initiator_id=token_payload.sub,
        user_to_kick_id=user_id,
        session=session,
    )
    return None
