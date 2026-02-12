import uuid

from httpx import AsyncClient
from integration.helpers import create_group, get_random_symbols, register_and_login, set_authorization
from starlette import status

from src.groups import group_router


async def test_get_mine_groups_success(client: AsyncClient):
    """
    Успешное получение своих групп
    """
    user = await register_and_login(client)
    await set_authorization(client, user)

    get_response = await client.get(f"{group_router.prefix}/mine/groups")
    assert get_response.json() == []

    random_symbols = get_random_symbols()
    random_symbols_2 = get_random_symbols()

    created_group_response_1 = await create_group(client, random_symbols, random_symbols, 31)
    created_group_response_2 = await create_group(client, random_symbols_2, random_symbols_2, 32)
    get_response = await client.get(f"{group_router.prefix}/mine/groups")

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()

    created_groups = [created_group_response_1.json(), created_group_response_2.json()]

    assert data[0]["id"] in [data["id"] for data in created_groups]
    assert data[1]["id"] in [data["id"] for data in created_groups]
    assert len(data) == 2


async def test_get_user_groups_success(client: AsyncClient):
    user1 = await register_and_login(client)
    await set_authorization(client, user1)

    random_symbols = get_random_symbols()
    random_symbols_2 = get_random_symbols()

    created_group_response_1 = await create_group(client, random_symbols, random_symbols, 31)
    created_group_response_2 = await create_group(client, random_symbols_2, random_symbols_2, 32)

    user2 = await register_and_login(client)
    await set_authorization(client, user2)

    get_response = await client.get(f"{group_router.prefix}/{user1['id']}/groups")

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()

    created_groups = [created_group_response_1.json(), created_group_response_2.json()]

    assert data[0]["id"] in [data["id"] for data in created_groups]
    assert data[1]["id"] in [data["id"] for data in created_groups]
    assert len(data) == 2


async def test_get_user_groups_no_user(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    get_response = await client.get(f"{group_router.prefix}/{uuid.uuid4()}/groups")

    assert get_response.status_code == status.HTTP_404_NOT_FOUND
