import uuid

from httpx import AsyncClient
from integration.helpers import (
    add_user_to_group,
    create_group,
    register_and_login,
    set_authorization,
)
from integration.helpers.group import add_permission
from starlette import status

from src.groups import GroupPermission, group_router


async def test_target_user_is_target_user(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user['id']}"
    )
    assert permission_response.status_code == status.HTTP_400_BAD_REQUEST


async def test_group_not_exists(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    permission_response = await client.delete(
        f"{group_router.prefix}/{str(uuid.uuid4())}/members/{str(uuid.uuid4())}"
    )
    assert permission_response.status_code == status.HTTP_404_NOT_FOUND


async def test_cant_kick_group_creator(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, create_group_response.json()["id"])

    await set_authorization(client, user2)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user['id']}"
    )
    assert permission_response.status_code == status.HTTP_403_FORBIDDEN


async def test_required_user_not_in_group(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{str(uuid.uuid4())}"
    )
    assert permission_response.status_code == status.HTTP_400_BAD_REQUEST
    assert permission_response.json()["detail"][0]["type"] == "group.required_user_not_in_group"


async def test_initiator_user_not_in_group(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)
    await add_user_to_group(client, user, user3, create_group_response.json()["id"])

    await set_authorization(client, user2)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user3['id']}"
    )
    assert permission_response.status_code == status.HTTP_400_BAD_REQUEST
    assert permission_response.json()["detail"][0]["type"] == "group.required_user_not_in_group"


async def test_no_permissions(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, create_group_response.json()["id"])
    await add_user_to_group(client, user, user3, create_group_response.json()["id"])

    await set_authorization(client, user2)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user3['id']}"
    )
    assert permission_response.status_code == status.HTTP_403_FORBIDDEN


async def test_full_access_cant_kick_full_access(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, create_group_response.json()["id"])
    await add_user_to_group(client, user, user3, create_group_response.json()["id"])
    await add_permission(client, user, user3, create_group_response.json()["id"], GroupPermission.FULL_ACCESS)
    await add_permission(client, user, user2, create_group_response.json()["id"], GroupPermission.FULL_ACCESS)

    await set_authorization(client, user2)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user3['id']}"
    )
    assert permission_response.status_code == status.HTTP_403_FORBIDDEN


async def test_success_full_access(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, create_group_response.json()["id"])
    await add_user_to_group(client, user, user3, create_group_response.json()["id"])
    await add_permission(client, user, user2, create_group_response.json()["id"], GroupPermission.FULL_ACCESS)

    await set_authorization(client, user2)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user3['id']}"
    )
    assert permission_response.status_code == status.HTTP_204_NO_CONTENT


async def test_success_group_creator(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, create_group_response.json()["id"])
    await add_permission(client, user, user2, create_group_response.json()["id"], GroupPermission.FULL_ACCESS)

    await set_authorization(client, user)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user2['id']}"
    )
    assert permission_response.status_code == status.HTTP_204_NO_CONTENT
