from fastapi import status
from httpx import AsyncClient

from src.auth import auth_router
from tests.integration.helpers import register_and_login


async def test_refresh_no_cookie(client: AsyncClient):
    """
    Проверяет поведение эндпоинта /refresh,
    если запрос отправлен без cookies с refresh_token.
    """
    response = await client.post(f"{auth_router.prefix}/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


async def test_refresh_invalid_token(client: AsyncClient):
    """
    Проверяет поведение эндпоинта /refresh,
    если в cookies передан некорректный refresh_token.
    """
    client.cookies.set("refresh_token", "INVALID_TOKEN")
    response = await client.post(f"{auth_router.prefix}/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


async def test_refresh_success(client: AsyncClient):
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


async def test_refresh_refresh_jti_not_valid(client: AsyncClient):
    """
    Проверяем, что после logout уже нельзя обновить refresh токен
    """
    user = await register_and_login(client)
    client.headers["Authorization"] = f"Bearer {user['access_token']}"
    response = await client.post(url=f"{auth_router.prefix}/logout")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    client.cookies.set("refresh_token", user["refresh_token"])

    response = await client.post(f"{auth_router.prefix}/refresh")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
