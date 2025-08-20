from httpx import AsyncClient
from starlette import status

from src.auth import auth_router
from tests.integration.helpers import register_and_login


async def test_change_password_no_cookie(client: AsyncClient):
    """
    Тестируем запрос без refresh_token cookie
    """
    user = await register_and_login(client)
    client.headers["Authorization"] = f"Bearer {user["access_token"]}"
    client.cookies.clear()
    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={"old_password": "1234567890", "new_password": "12345678901"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] is not None


async def test_change_password_invalid_token(client: AsyncClient):
    """
    Тестируем запрос с некорректным refresh_token
    """
    user = await register_and_login(client)
    client.headers["Authorization"] = f"Bearer {user["access_token"]}"
    client.cookies.set("refresh_token", "INVALID_TOKEN")
    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={"old_password": "1234567890", "new_password": "12345678901"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] is not None


async def test_change_password_same_password(client: AsyncClient):
    """
    Старый и новый пароли совпадают → ошибка
    """
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user["access_token"]}"
    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={
            "old_password": user["payload"]["password"],
            "new_password": user["payload"]["password"],
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] is not None


async def test_change_password_wrong_old(client: AsyncClient):
    """
    Передан неверный старый пароль
    """
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user["access_token"]}"
    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={
            "old_password": "WRONG!OLD",
            "new_password": "NEW!SECRET123",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    print(response.json())
    assert response.json()["detail"] is not None


async def test_change_password_success(client: AsyncClient):
    """
    Успешная смена пароля + проверка входа новым паролем
    """
    user = await register_and_login(client)

    old_password = user["payload"]["password"]
    new_password = old_password + "!new"

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user["access_token"]}"

    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={
            "old_password": old_password,
            "new_password": new_password,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert "success" in response.json()

    response = await client.post(
        f"{auth_router.prefix}/sign_in",
        json={
            "identifier": user["payload"]["login"],
            "password": old_password,
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = await client.post(
        f"{auth_router.prefix}/sign_in",
        json={
            "identifier": user["payload"]["login"],
            "password": new_password,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

async def test_change_password_refresh_jti_not_valid(client: AsyncClient):
    """
    Проверяем, что после logout уже нельзя изменить пароль
    """
    user = await register_and_login(client)
    client.headers["Authorization"] = f"Bearer {user["access_token"]}"
    response = await client.post(url=f"{auth_router.prefix}/logout")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    old_password = user["payload"]["password"]
    new_password = old_password + "!new"

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user["access_token"]}"

    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={
            "old_password": old_password,
            "new_password": new_password,
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED