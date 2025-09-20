from httpx import AsyncClient
from integration.helpers import create_group, get_random_symbols, register_and_login, set_authorization
from starlette import status

from src.groups import group_router


async def test_search_groups_ilike_p(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = await get_random_symbols()

    resp = await create_group(client, f"{random_symbols}_123")
    assert resp.status_code == status.HTTP_201_CREATED

    get_response = await client.get(f"{group_router.prefix}/search", params={"name": random_symbols})

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()

    assert data[0]["id"] == resp.json()["id"]


async def test_search_groups_p_ilike_p(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = await get_random_symbols()
    random_adds = await get_random_symbols(4)

    resp1 = await create_group(client, f"{random_symbols}_{random_adds}")
    assert resp1.status_code == status.HTTP_201_CREATED
    resp2 = await create_group(client, f"{random_adds}_{random_symbols}_{random_adds}")
    assert resp2.status_code == status.HTTP_201_CREATED

    get_response = await client.get(f"{group_router.prefix}/search", params={"name": random_symbols})

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()

    assert data[0]["id"] == resp1.json()["id"]
    assert data[1]["id"] == resp2.json()["id"]


async def test_search_groups_trigram(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_for_trigram = await get_random_symbols()
    random_symbols = await get_random_symbols(8)

    resp1 = await create_group(client, f"{random_for_trigram}_{random_symbols}")
    assert resp1.status_code == status.HTTP_201_CREATED
    resp2 = await create_group(client, f"{random_for_trigram}_{random_symbols}_{random_symbols}")
    assert resp2.status_code == status.HTTP_201_CREATED

    get_response = await client.get(f"{group_router.prefix}/search", params={"name": random_for_trigram})

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()

    assert data[0]["id"] == resp1.json()["id"]
    assert data[1]["id"] == resp2.json()["id"]


async def test_search_groups_limit(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_for_trigram = await get_random_symbols()
    random_symbols = await get_random_symbols(8)

    resp1 = await create_group(client, f"{random_for_trigram}_{random_symbols}")
    assert resp1.status_code == status.HTTP_201_CREATED
    resp2 = await create_group(client, f"{random_for_trigram}_{random_symbols}_{random_symbols}")
    assert resp2.status_code == status.HTTP_201_CREATED

    get_response = await client.get(f"{group_router.prefix}/search", params={"name": random_for_trigram})

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()

    assert data[0]["id"] == resp1.json()["id"]
    assert data[1]["id"] == resp2.json()["id"]

    get_response = await client.get(
        f"{group_router.prefix}/search", params={"name": random_for_trigram, "limit": 1}
    )

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()

    assert data[0]["id"] == resp1.json()["id"]
    assert len(data) == 1


async def test_search_groups_offset(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_for_trigram = await get_random_symbols()
    random_symbols = await get_random_symbols(8)

    resp1 = await create_group(client, f"{random_for_trigram}_{random_symbols}")
    assert resp1.status_code == status.HTTP_201_CREATED
    resp2 = await create_group(client, f"{random_for_trigram}_{random_symbols}_{random_symbols}")
    assert resp2.status_code == status.HTTP_201_CREATED

    get_response = await client.get(f"{group_router.prefix}/search", params={"name": random_for_trigram})

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()

    assert data[0]["id"] == resp1.json()["id"]
    assert data[1]["id"] == resp2.json()["id"]

    get_response = await client.get(
        f"{group_router.prefix}/search", params={"name": random_for_trigram, "limit": 1, "offset": 1}
    )

    assert get_response.status_code == status.HTTP_200_OK
    data = get_response.json()

    assert data[0]["id"] == resp2.json()["id"]
    assert len(data) == 1
