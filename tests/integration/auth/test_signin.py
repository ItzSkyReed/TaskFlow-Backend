import uuid

from starlette import status

from src.auth import auth_router
from tests.conftest import settings


async def test_valid_sign_in(client):
    # Сначала регистрируем пользователя
    unique = uuid.uuid4().hex[:16]
    payload = {
        "name": f"User{unique}",
        "login": f"User{unique}",
        "email": f"user{unique}@example.com",
        "password": f"Pass{unique}word",
    }
    await client.post(f"{auth_router.prefix}/sign_up", json=payload)

    # Теперь логинимся
    signin_payload = {
        "identifier": payload["login"],
        "password": payload["password"],
    }
    response = await client.post(f"{auth_router.prefix}/sign_in", json=signin_payload)

    assert response.status_code == status.HTTP_200_OK

    # Проверяем, что в JSON вернулся access_token
    data = response.json()
    assert "access_token" in data, "access_token должен вернуться при успешном входе"
    assert isinstance(data["access_token"], str)

    # Проверяем refresh_token cookie
    cookie_value = response.cookies.get("refresh_token")
    assert cookie_value is not None, "refresh_token cookie должен быть установлен"

    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any("refresh_token=" in h for h in set_cookie_headers), (
        "Нет refresh_token в Set-Cookie"
    )
    assert any("HttpOnly" in h for h in set_cookie_headers), (
        "refresh_token должен быть HttpOnly"
    )

    expected_path = f"{settings.root_path}{settings.api_prefix}{auth_router.prefix}"
    assert any(f"Path={expected_path}" in h for h in set_cookie_headers), (
        f"Path у куки должен быть {expected_path}"
    )
    assert response.json()["detail"] is not None


async def test_sign_in_invalid_password(client):
    unique = uuid.uuid4().hex[:16]
    payload = {
        "name": f"User{unique}",
        "login": f"User{unique}",
        "email": f"user{unique}@example.com",
        "password": f"Pass{unique}word",
    }
    await client.post(f"{auth_router.prefix}/sign_up", json=payload)

    # Логинимся с неправильным паролем
    signin_payload = {"identifier": payload["login"], "password": "WrongPassword123"}
    response = await client.post(f"{auth_router.prefix}/sign_in", json=signin_payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] is not None


async def test_sign_in_user_not_found(client):
    # Логинимся под несуществующим пользователем
    signin_payload = {"identifier": "NoSuchUser", "password": "somepassword"}
    response = await client.post(f"{auth_router.prefix}/sign_in", json=signin_payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] is not None


async def test_sign_in_invalid_schema(client):
    # Передаем некорректный payload
    signin_payload = {
        "identifier": 123,  # должен быть str
        "password": 456,  # должен быть str
    }
    response = await client.post(f"{auth_router.prefix}/sign_in", json=signin_payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"] is not None
