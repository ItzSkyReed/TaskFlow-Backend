import uuid

from httpx import AsyncClient
from integration.helpers import get_random_symbols, register_and_login
from integration.helpers.group import create_group
from integration.helpers.user import set_authorization
from starlette import status

from src.groups import group_router


async def test_get_group_success(client: AsyncClient):
    """
    Успешный фетч группы
    """
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = await get_random_symbols()
    create_group_response = await create_group(client, random_symbols, random_symbols, 31)

    get_response = await client.get(f"{group_router.prefix}/{create_group_response.json()['id']}")

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()
    assert data["name"] == random_symbols
    assert data["description"] == random_symbols
    assert data["max_members_count"] == 31
    assert data["members"][0]["user"]["id"] == user["id"]


async def test_get_no_group(client: AsyncClient):
    """
    Фетч не найденной группы
    """
    user = await register_and_login(client)
    await set_authorization(client, user)

    get_response = await client.get(f"{group_router.prefix}/{uuid.uuid4()}")

    assert get_response.status_code == status.HTTP_404_NOT_FOUND
