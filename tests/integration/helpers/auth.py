import uuid

from starlette import status

from src.auth import auth_router


async def register_and_login(client, unique=None):
    if unique is None:
        unique = uuid.uuid4().hex[:16]

    payload = {
        "name": f"User{unique}",
        "login": f"user{unique}",
        "email": f"user{unique}@example.com",
        "password": unique,
    }

    # Регистрация
    response = await client.post(f"{auth_router.prefix}/sign_up", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    refresh_token = response.cookies.get("refresh_token")
    access_token = response.json().get("access_token")

    return {
        "payload": payload,
        "refresh_token": refresh_token,
        "access_token": access_token,
    }