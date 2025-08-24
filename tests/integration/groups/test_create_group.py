from httpx import AsyncClient
from starlette import status

from src.groups import group_router
from src.groups.constants import MAX_CREATED_GROUPS
from tests.integration.helpers import (
    get_random_symbols,
    get_token_payload,
    register_and_login,
)


async def test_create_group_success(client: AsyncClient):
    """Успешное создание группы без приглашений"""
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user['access_token']}"
    random_symbols = await get_random_symbols()
    response = await client.post(
        f"{group_router.prefix}",
        json={
            "name": random_symbols,
            "description": "Test group",
            "max_members_count": 10,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == random_symbols
    assert data["creator_id"] == (await get_token_payload(user["refresh_token"]))["sub"]


async def test_create_group_success_no_members(client: AsyncClient):
    """Успешное создание группы без приглашений"""
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user['access_token']}"
    random_symbols = await get_random_symbols()
    response = await client.post(
        f"{group_router.prefix}",
        json={
            "name": random_symbols,
            "description": "Test group",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == random_symbols
    assert data["creator_id"] == (await get_token_payload(user["refresh_token"]))["sub"]


async def test_create_group_max_members_too_big(client: AsyncClient):
    """Успешное создание группы без приглашений"""
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user['access_token']}"

    response = await client.post(
        f"{group_router.prefix}",
        json={
            "name": f"My First Group_{await get_random_symbols()}",
            "description": "Test group",
            "max_members_count": 1000,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_create_group_max_members_too_small(client: AsyncClient):
    """Успешное создание группы без приглашений"""
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user['access_token']}"

    response = await client.post(
        f"{group_router.prefix}",
        json={
            "name": f"My First Group_{await get_random_symbols()}",
            "description": "Test group",
            "max_members_count": 1,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_create_group_no_name(client: AsyncClient):
    """Успешное создание группы без приглашений"""
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user['access_token']}"

    response = await client.post(
        f"{group_router.prefix}",
        json={
            "description": "Test group",
            "max_members_count": 10,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_create_group_with_invitations(client: AsyncClient):
    """Успешное создание группы с приглашениями"""
    owner = await register_and_login(client)
    invitee = await register_and_login(client)  # другой пользователь

    invitee_id = (await get_token_payload(invitee["refresh_token"]))["sub"]

    client.cookies.set("refresh_token", owner["refresh_token"])
    client.headers["Authorization"] = f"Bearer {owner['access_token']}"

    response = await client.post(
        f"{group_router.prefix}",
        json={
            "name": f"Group With Invites_{await get_random_symbols()}",
            "description": "Test with invites",
            "max_members_count": 5,
            "invitations": [invitee_id],
        },
    )

    assert response.status_code == status.HTTP_201_CREATED


async def test_create_group_limit_exceeded(client: AsyncClient):
    """Превышен лимит создания групп"""
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user['access_token']}"

    for i in range(MAX_CREATED_GROUPS):
        response = await client.post(
            f"{group_router.prefix}",
            json={
                "name": f"Group{i}_{await get_random_symbols()}",
                "description": "Test",
                "max_members_count": 5,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    response = await client.post(
        f"{group_router.prefix}",
        json={
            "name": f"OverflowGroup_{await get_random_symbols()}",
            "description": "Should fail",
            "max_members_count": 5,
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_create_group_duplicate_name(client: AsyncClient):
    """Попытка создать группу с тем же именем"""
    user = await register_and_login(client)

    client.cookies.set("refresh_token", user["refresh_token"])
    client.headers["Authorization"] = f"Bearer {user['access_token']}"

    random_symbols = await get_random_symbols()
    body = {
        "name": f"UniqueGroup_{random_symbols}",
        "description": "Test",
        "max_members_count": 5,
    }

    # первая успешная
    response = await client.post(f"{group_router.prefix}", json=body)
    assert response.status_code == status.HTTP_201_CREATED

    # дубликат
    response = await client.post(f"{group_router.prefix}", json=body)
    assert response.status_code == status.HTTP_409_CONFLICT


async def test_create_group_unauthorized(client: AsyncClient):
    """Без access_token → 401"""
    response = await client.post(
        f"{group_router.prefix}",
        json={
            "name": "UnauthorizedGroup",
            "description": "Should fail",
            "max_members_count": 5,
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
