from httpx import AsyncClient
from integration.helpers import (
    add_user_to_group,
    create_group,
    get_random_symbols,
    register_and_login,
    set_authorization,
)
from integration.helpers.group import add_permission
from starlette import status

from src.groups import GroupPermission, group_router


async def test_success(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    random_symbols = get_random_symbols()
    group_resp = await create_group(client, f"old_name{random_symbols}", f"old_desc{random_symbols}", 5)
    group_id = group_resp.json()["id"]

    patch_data = {
        "name": f"new_name{random_symbols}",
        "description": f"new_desc{random_symbols}",
        "max_members_count": 10,
    }
    resp = await client.patch(f"{group_router.prefix}/{group_id}", json=patch_data)

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["name"] == f"new_name{random_symbols}"
    assert data["description"] == f"new_desc{random_symbols}"
    assert data["max_members_count"] == 10


async def test_success_full_access(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    group_resp = await create_group(client)
    group_id = group_resp.json()["id"]

    await add_user_to_group(client, user, user2, group_id)
    await add_permission(client, user, user2, group_id, GroupPermission.FULL_ACCESS)

    await set_authorization(client, user2)
    patch_data = {
        "max_members_count": 10,
    }
    resp = await client.patch(f"{group_router.prefix}/{group_id}", json=patch_data)

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["max_members_count"] == 10


async def test_success_manage_group(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    group_resp = await create_group(client)
    group_id = group_resp.json()["id"]

    await add_user_to_group(client, user, user2, group_id)
    await add_permission(client, user, user2, group_id, GroupPermission.MANAGE_GROUP)

    await set_authorization(client, user2)
    patch_data = {
        "max_members_count": 10,
    }
    resp = await client.patch(f"{group_router.prefix}/{group_id}", json=patch_data)

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["max_members_count"] == 10


async def test_success_no_name(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    random_symbols = get_random_symbols()
    group_resp = await create_group(client, f"old_name{random_symbols}", f"old_desc{random_symbols}", 5)
    group_id = group_resp.json()["id"]

    patch_data = {
        "name": f"new_name{random_symbols}",
        "description": f"new_desc{random_symbols}",
        "max_members_count": 10,
    }
    resp = await client.patch(f"{group_router.prefix}/{group_id}", json=patch_data)

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["description"] == f"new_desc{random_symbols}"
    assert data["max_members_count"] == 10


async def test_too_many_members(client: AsyncClient):
    user1 = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user1)

    group_resp = await create_group(client)
    group_id = group_resp.json()["id"]

    await add_user_to_group(client, user1, user2, group_id)
    await add_user_to_group(client, user1, user3, group_id)

    patch_data = {"max_members_count": 2}
    resp = await client.patch(f"{group_router.prefix}/{group_id}", json=patch_data)
    assert resp.status_code == status.HTTP_409_CONFLICT


async def test_patch_group_no_permission(client: AsyncClient):
    user1 = await register_and_login(client)
    await set_authorization(client, user1)
    random_symbols = get_random_symbols()
    group_resp = await create_group(client, f"group_perm_test{random_symbols}", f"desc{random_symbols}", 5)
    group_id = group_resp.json()["id"]

    user2 = await register_and_login(client)

    await set_authorization(client, user2)
    patch_data = {"name": f"hacked_name{random_symbols}"}
    resp = await client.patch(f"{group_router.prefix}/{group_id}", json=patch_data)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


async def test_patch_group_duplicate_name(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    random_symbols = get_random_symbols()
    # Создаём две группы
    await create_group(client, f"group1{random_symbols}", f"desc{random_symbols}")
    group2 = await create_group(client, f"group2{random_symbols}", f"desc{random_symbols}")
    group2_id = group2.json()["id"]

    patch_data = {"name": f"group1{random_symbols}"}  # Попытка задать дублирующее имя
    resp = await client.patch(f"{group_router.prefix}/{group2_id}", json=patch_data)
    assert resp.status_code == status.HTTP_409_CONFLICT
