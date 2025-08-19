from starlette import status

from src.auth import auth_router
from tests.integration.helpers import register_and_login


async def test_change_password_no_cookie(client):
    """
    Тестируем запрос без refresh_token cookie
    """
    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={"old_password": "123", "new_password": "456"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


async def test_change_password_invalid_token(client):
    """
    Тестируем запрос с некорректным refresh_token
    """
    client.cookies.set("refresh_token", "INVALID_TOKEN")
    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={"old_password": "123", "new_password": "456"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


async def test_change_password_same_password(client):
    """
    Старый и новый пароли совпадают → ошибка
    """
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={
            "old_password": user["payload"]["password"],
            "new_password": user["payload"]["password"],
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


async def test_change_password_wrong_old(client):
    """
    Передан неверный старый пароль
    """
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={
            "old_password": "WRONG_OLD",
            "new_password": "NEW_SECRET123",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] is not None


async def test_change_password_success(client):
    """
    Успешная смена пароля + проверка входа новым паролем
    """
    user = await register_and_login(client)

    old_password = user["payload"]["password"]
    new_password = old_password + "_new"

    client.cookies.set("refresh_token", user["refresh_token"])
    response = await client.post(
        f"{auth_router.prefix}/change_password",
        json={
            "old_password": old_password,
            "new_password": new_password,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "success" in data

    response = await client.post(
        f"{auth_router.prefix}/sign_in",
        json={
            "identifier": user["payload"]["login"],
            "password": old_password,
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = await client.post(
        f"{auth_router.prefix}/sign_in",
        json={
            "identifier": user["payload"]["login"],
            "password": new_password,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
