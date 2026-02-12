import uuid

from httpx import AsyncClient
from integration.helpers import create_group, get_random_symbols, register_and_login, set_authorization
from starlette import status

from src.groups import group_router


async def test_delete_group_success(client: AsyncClient):
    """
    Успешное удаление группы
    """
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = get_random_symbols()
    create_group_response = await create_group(client, random_symbols, random_symbols, 31)

    get_response = await client.get(f"{group_router.prefix}/{create_group_response.json()['id']}")

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()
    assert data["name"] == random_symbols
    assert data["description"] == random_symbols
    assert data["max_members_count"] == 31
    assert data["members"][0]["user"]["id"] == user["id"]

    delete_response = await client.delete(f"{group_router.prefix}/{create_group_response.json()['id']}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


async def test_delete_group_no_group(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    delete_response = await client.delete(f"{group_router.prefix}/{uuid.uuid4()}")

    assert delete_response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_group_no_permissons(client: AsyncClient):
    """
    Недостаточно прав для удаление группы
    """
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = get_random_symbols()
    create_group_response = await create_group(client, random_symbols, random_symbols, 31)

    get_response = await client.get(f"{group_router.prefix}/{create_group_response.json()['id']}")

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()
    assert data["name"] == random_symbols
    assert data["description"] == random_symbols
    assert data["max_members_count"] == 31
    assert data["members"][0]["user"]["id"] == user["id"]

    user2 = await register_and_login(client)
    await set_authorization(client, user2)

    delete_response = await client.delete(f"{group_router.prefix}/{create_group_response.json()['id']}")
    assert delete_response.status_code == status.HTTP_403_FORBIDDEN
