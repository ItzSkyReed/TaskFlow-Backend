import pytest
from fastapi import status

from src.auth import auth_router
from tests.integration.helpers import register_and_login


@pytest.mark.asyncio
async def test_refresh_no_cookie(client):
    """
    Проверяет поведение эндпоинта /refresh,
    если запрос отправлен без cookies с refresh_token.
    """
    response = await client.post(f"{auth_router.prefix}/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    """
    Проверяет поведение эндпоинта /refresh,
    если в cookies передан некорректный refresh_token.
    """
    client.cookies.set("refresh_token", "INVALID_TOKEN")
    response = await client.post(f"{auth_router.prefix}/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


@pytest.mark.asyncio
async def test_refresh_success(client):
    """
    Проверяет успешное обновление access_token по refresh_token
    - сохраняем refresh_token в cookies
    - вызываем /refresh
    - убеждаемся, что access_token обновился, а refresh_token в cookie поменялся
    """
    user = await register_and_login(client)

    old_refresh_token = user["refresh_token"]
    client.cookies.set("refresh_token", old_refresh_token)

    response = await client.post(f"{auth_router.prefix}/refresh")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert "refresh_token" not in data

    # Проверяем, что refresh_token в cookie обновился
    new_refresh_token = response.cookies.get("refresh_token")
    assert new_refresh_token != old_refresh_token
