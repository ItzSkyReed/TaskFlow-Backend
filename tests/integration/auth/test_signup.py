import uuid

import pytest
from starlette import status

from src.auth import auth_router
from tests.conftest import settings

@pytest.mark.order(1)
async def test_valid_sign_up(client):
    unique = uuid.uuid4().hex[:16]
    payload = {
        "name": f"Joe_Sardina{unique}",
        "login": f"Joe_Sardina{unique}",
        "email": f"johndoe{unique}@example.com",
        "password": unique,
    }

    response = await client.post(f"{auth_router.prefix}/sign_up", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.order(1)
async def test_valid_sign_up_cookies(client):
    unique = uuid.uuid4().hex[:16]
    payload = {
        "name": f"Joe_Sardina{unique}",
        "login": f"Joe_Sardina{unique}",
        "email": f"johndoe{unique}@example.com",
        "password": unique,
    }

    response = await client.post(f"{auth_router.prefix}/sign_up", json=payload)

    cookie_value = response.cookies.get("refresh_token")
    assert cookie_value is not None, "refresh_token cookie должен быть установлен"

    # Проверка заголовка Set-Cookie
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

@pytest.mark.order(1)
async def test_conflict_sign_up(client):
    unique = uuid.uuid4().hex[:16]
    payload = {
        "name": f"User{unique}",
        "login": f"User{unique}",
        "email": f"user{unique}@example.com",
        "password": f"Pass{unique}word",
    }
    # Первый запрос должен пройти успешно
    response1 = await client.post(f"{auth_router.prefix}/sign_up", json=payload)
    assert response1.status_code == status.HTTP_201_CREATED

    # Второй запрос с тем же логином и email должен вернуть конфликт
    response2 = await client.post(f"{auth_router.prefix}/sign_up", json=payload)
    assert response2.status_code == status.HTTP_409_CONFLICT

    assert response2.json()["detail"] is not None

@pytest.mark.order(1)
async def test_conflict_sign_up_email_only(client):
    unique1 = uuid.uuid4().hex[:16]
    unique2 = uuid.uuid4().hex[:16]
    payload1 = {
        "name": f"User{unique1}",
        "login": f"User{unique1}",
        "email": f"user{unique1}@example.com",
        "password": f"Pass{unique1}word",
    }
    payload2 = {
        "name": f"User{unique2}",
        "login": f"User{unique2}",
        "email": f"user{unique1}@example.com",  # одинаковый email
        "password": f"Pass{unique2}word",
    }
    await client.post(f"{auth_router.prefix}/sign_up", json=payload1)
    response = await client.post(f"{auth_router.prefix}/sign_up", json=payload2)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] is not None

@pytest.mark.order(1)
async def test_conflict_sign_up_login_only(client):
    unique1 = uuid.uuid4().hex[:16]
    unique2 = uuid.uuid4().hex[:16]
    payload1 = {
        "name": f"User{unique1}",
        "login": f"User{unique1}",
        "email": f"user{unique1}@example.com",
        "password": f"Pass{unique1}word",
    }
    payload2 = {
        "name": f"User{unique2}",
        "login": f"User{unique1}",  # одинаковый login
        "email": f"user{unique2}@example.com",
        "password": f"Pass{unique2}word",
    }
    await client.post(f"{auth_router.prefix}/sign_up", json=payload1)
    response = await client.post(f"{auth_router.prefix}/sign_up", json=payload2)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] is not None

@pytest.mark.order(1)
async def test_invalid_schema_sign_up(client):
    payload = {"name": "A", "login": "ab", "email": "not-an-email", "password": "123"}
    response = await client.post(f"{auth_router.prefix}/sign_up", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json()["detail"] is not None
