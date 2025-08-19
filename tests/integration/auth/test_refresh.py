import uuid

import pytest
from fastapi import status

from src.auth import auth_router

async def test_refresh_no_cookie(client):
    """
    Тестируем запрос без cookies
    """
    response = await client.post(f"{auth_router.prefix}/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


async def test_refresh_invalid_token(client):
    """
    Тестируем запрос с некорректным refresh токеном
    """
    client.cookies.set("refresh_token", "INVALID_TOKEN")
    response = await client.post(f"{auth_router.prefix}/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


async def test_refresh_success(client):
    """
    Тестируем успешное обновление токена
    """
    unique = uuid.uuid4().hex[:16]
    payload = {
        "name": f"Joe_Sardina{unique}",
        "login": f"Joe_Sardina{unique}",
        "email": f"johndoe{unique}@example.com",
        "password": unique,
    }

    response = await client.post(f"{auth_router.prefix}/sign_up", json=payload)
    refresh_token = response.cookies.get("refresh_token")
    client.cookies.set("refresh_token", refresh_token)
    response = await client.post(f"{auth_router.prefix}/refresh")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert "refresh_token" not in data
    # Проверяем, что cookie обновилась
    new_refresh_token = response.cookies.get("refresh_token")
    assert new_refresh_token != refresh_token
