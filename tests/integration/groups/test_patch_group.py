from httpx import AsyncClient
from integration.helpers import create_group, get_random_symbols, register_and_login, set_authorization
from starlette import status

from src.groups import group_router


async def test_patch_group_success(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    random_symbols = await get_random_symbols()
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


# TODO нужно доделать после join_request/invite
# async def test_patch_group_size_conflict(client: AsyncClient):
#     user = await register_and_login(client)
#     await set_authorization(client, user)
#     random_symbols = await get_random_symbols()
#     group_resp = await create_group(client, f"group_size_test{random_symbols}", max_members_count=3)
#     group_id = group_resp.json()["id"]
#
#
#     patch_data = {"max_members_count": 2}
#     resp = await client.patch(f"{group_router.prefix}/{group_id}", json=patch_data)
#     assert resp.status_code == status.HTTP_400_BAD_REQUEST
#     assert resp.json()["err_type"] == "group.size.conflict"


async def test_patch_group_no_permission(client: AsyncClient):
    user1 = await register_and_login(client)
    await set_authorization(client, user1)
    random_symbols = await get_random_symbols()
    group_resp = await create_group(client, f"group_perm_test{random_symbols}", f"desc{random_symbols}", 5)
    group_id = group_resp.json()["id"]

    user2 = await register_and_login(client)
    await set_authorization(client, user2)

    patch_data = {"name": f"hacked_name{random_symbols}"}
    resp = await client.patch(f"{group_router.prefix}/{group_id}", json=patch_data)
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert resp.json()["err_type"] == "group.not_enough_permissions"


async def test_patch_group_duplicate_name(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    random_symbols = await get_random_symbols()
    # Создаём две группы
    await create_group(client, f"group1{random_symbols}", f"desc{random_symbols}")
    group2 = await create_group(client, f"group2{random_symbols}", f"desc{random_symbols}")
    group2_id = group2.json()["id"]

    patch_data = {"name": f"group1{random_symbols}"}  # Попытка задать дублирующее имя
    resp = await client.patch(f"{group_router.prefix}/{group2_id}", json=patch_data)
    assert resp.status_code == status.HTTP_409_CONFLICT
    assert resp.json()["err_type"] == "group.with_such_name_already_exists"
