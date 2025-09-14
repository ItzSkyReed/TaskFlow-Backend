import base64
import uuid
from typing import TypedDict

import orjson
from httpx import AsyncClient
from starlette import status

from src.auth import auth_router
from src.user import profile_router


class PayloadDict(TypedDict):
    name: str
    login: str
    email: str
    password: str


class AuthResult(TypedDict):
    payload: PayloadDict
    refresh_token: str
    access_token: str
    id: uuid.UUID


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
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    profile_response = await client.get(f"{profile_router.prefix}/me")

    return {
        "payload": payload,
        "refresh_token": response.cookies["refresh_token"],
        "access_token": response.json()["access_token"],
        "id": profile_response.json()["id"],
    }


async def get_token_payload(token: str) -> dict:
    return orjson.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))


async def set_authorization(
    client: AsyncClient,
    user: AuthResult,
):
    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user['access_token']}"
