from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ..auth.schemas import TokenPayloadSchema
from ..auth.security import token_verification
from ..database import get_async_session
from ..schemas import ErrorResponseModel
from .schemas import CreateGroupSchema, GroupSchema
from .usecases import create_group

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
        429: {"description": "Превышены лимиты API.", "model": ErrorResponseModel},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[Depends(RateLimiter(times=30, minutes=1))],
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
