from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

from ..database import get_async_session
from ..schemas import SuccessResponseModel
from .config import get_auth_settings
from .dependencies import validate_user_uniqueness
from .exceptions import RefreshTokenNotFound
from .schemas import (
    AccessTokenSchema,
    ChangePasswordSchema,
    SignInSchema,
    SignUpSchema,
)
from .security import token_verification
from .usecases import (
    change_user_password,
    logout_user,
    refresh_user_tokens,
    sign_in_user,
    sign_up_user,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentification"])

auth_settings = get_auth_settings()


@auth_router.post(
    "/sign_up",
    name="Регистрация нового пользователя",
    response_model=AccessTokenSchema,
    status_code=status.HTTP_201_CREATED,
    description="Регистрация нового пользователя",
    responses={
        201: {"description": "Успешная регистрация"},
        400: {"description": "Некорректные данные в запросе."},
        409: {"description": "Пользователь с таким логином или email уже существует."},
        422: {"description": "Некорректные данные в запросе (валидация схемы)."},
        429: {"description": "Превышены лимиты API."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[Depends(RateLimiter(times=1000, minutes=5))],
)
async def sign_up_user_route(
    response: Response,
    user_in: Annotated[SignUpSchema, Depends(validate_user_uniqueness)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AccessTokenSchema:
    register_result = await sign_up_user(user_in, session)

    response.set_cookie(
        key="refresh_token",
        value=register_result.refresh_token,
        httponly=True,
        max_age=auth_settings.refresh_token_expires_in,
        path=auth_router.prefix,
    )

    return AccessTokenSchema(access_token=register_result.access_token)


@auth_router.post(
    "/sign_in",
    name="Вход пользователя в систему",
    response_model=AccessTokenSchema,
    status_code=status.HTTP_200_OK,
    description="Вход пользователя в систему",
    responses={
        200: {"description": "Успешный вход"},
        400: {"description": "Некорректные данные в запросе."},
        401: {"description": "Логин/Емаил/Пароль неверные или JWT токен поврежден"},
        404: {"description": "Пользователь не найден"},
        422: {"description": "Некорректные данные в запросе (валидация схемы)."},
        429: {"description": "Превышены лимиты API."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[Depends(RateLimiter(times=3000, minutes=5))],
)
async def sign_in_user_route(
    response: Response,
    user_in: Annotated[SignInSchema, Body(...)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> AccessTokenSchema:
    login_result = await sign_in_user(user_in, session)

    response.set_cookie(
        key="refresh_token",
        value=login_result.refresh_token,
        httponly=True,
        max_age=auth_settings.refresh_token_expires_in,
        path=auth_router.prefix,
    )

    return AccessTokenSchema(access_token=login_result.access_token)


@auth_router.post(
    "/refresh",
    name="Обновление токенов",
    response_model=AccessTokenSchema,
    status_code=status.HTTP_200_OK,
    description="Обновление токенов",
    responses={
        200: {"description": "Успешное обновление токена"},
        400: {"description": "Некорректные данные в запросе."},
        401: {"description": "RefreshToken не найден, истек или некорректен"},
        429: {"description": "Превышены лимиты API."},
        422: {"description": "Некорректные данные в запросе (валидация схемы)."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[Depends(RateLimiter(times=20, minutes=5))],
)
async def refresh_tokens_route(
    request: Request, response: Response
) -> AccessTokenSchema:
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise RefreshTokenNotFound()

    new_tokens = await refresh_user_tokens(refresh_token)

    response.set_cookie(
        key="refresh_token",
        value=new_tokens.refresh_token,
        httponly=True,
        max_age=auth_settings.refresh_token_expires_in,
        path=auth_router.prefix,
    )

    return AccessTokenSchema(access_token=new_tokens.access_token)


@auth_router.post(
    "/change_password",
    name="Смена пароля",
    status_code=status.HTTP_200_OK,
    response_model=SuccessResponseModel,
    description="Изменение пароля на новый",
    responses={
        200: {"description": "Успешная смена пароля"},
        400: {"description": "Некорректные данные в запросе."},
        401: {"description": "RefreshToken не найден, истек или некорректен"},
        403: {"description": "Старый пароль не верный"},
        404: {"description": "Пользователь не найден"},
        422: {"description": "Некорректные данные в запросе (валидация схемы)."},
        429: {"description": "Превышены лимиты API."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    dependencies=[
        Depends(token_verification),
        Depends(RateLimiter(times=20, minutes=5)),
    ],
)
async def change_password_route(
    request: Request,
    passwords: Annotated[ChangePasswordSchema, Body(...)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> SuccessResponseModel:
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise RefreshTokenNotFound()

    await change_user_password(passwords, refresh_token, session)

    return SuccessResponseModel()


@auth_router.post(
    "/logout",
    name="Выход",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    description="При выходе будет удален refresh токен из куки + БД сервера",
    responses={
        204: {"description": "Успешный выход"},
        400: {"description": "Некорректные данные в запросе."},
        401: {"description": "RefreshToken не найден, истек или некорректен"},
        500: {"description": "Внутренняя ошибка сервера."},
    },
)
async def logout_user_route(request: Request, response: Response) -> None:
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise RefreshTokenNotFound()

    await logout_user(refresh_token)

    response.delete_cookie(
        key="refresh_token",
        path=auth_router.prefix,
    )

    return None
