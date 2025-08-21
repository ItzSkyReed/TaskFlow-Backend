import uuid
from typing import TypedDict

from httpx import AsyncClient
from starlette import status

from src.auth import auth_router


class PayloadDict(TypedDict):
    name: str
    login: str
    email: str
    password: str


class AuthResult(TypedDict):
    payload: PayloadDict
    refresh_token: str
    access_token: str


async def register_and_login(client: AsyncClient, unique=None) -> AuthResult:
    if unique is None:
        unique = uuid.uuid4().hex[:16]

    payload = PayloadDict(
        name=f"User{unique}",
        login=f"user{unique}",
        email=f"user{unique}@example.com",
        password=unique,
    )

    # Регистрация
    response = await client.post(f"{auth_router.prefix}/sign_up", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    refresh_token = response.cookies["refresh_token"]
    access_token = response.json()["access_token"]

    return {
        "payload": payload,
        "refresh_token": refresh_token,
        "access_token": access_token,
    }
