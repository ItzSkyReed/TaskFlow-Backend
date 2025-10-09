from httpx import AsyncClient
from integration.helpers import (
    add_user_to_group,
    create_group,
    register_and_login,
    set_authorization,
)
from starlette import status

from src.groups import GroupPermission, group_router


async def test_target_user_is_changer_user(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user['id']}/{GroupPermission.INVITE_MEMBERS.value}"
    )
    assert permission_response.status_code == status.HTTP_409_CONFLICT


async def test_changer_member_not_in_group(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await set_authorization(client, user2)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user3['id']}/{GroupPermission.INVITE_MEMBERS.value}"
    )
    assert permission_response.status_code == status.HTTP_400_BAD_REQUEST


async def test_target_member_not_in_group(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)
    await add_user_to_group(client, user, user2, create_group_response.json()["id"])

    await set_authorization(client, user2)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user3['id']}/{GroupPermission.INVITE_MEMBERS.value}"
    )
    assert permission_response.status_code == status.HTTP_400_BAD_REQUEST


async def test_no_control_members_permission(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)
    await add_user_to_group(client, user, user2, create_group_response.json()["id"])
    await add_user_to_group(client, user, user3, create_group_response.json()["id"])

    await set_authorization(client, user3)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user2['id']}/{GroupPermission.INVITE_MEMBERS.value}"
    )
    assert permission_response.status_code == status.HTTP_403_FORBIDDEN


async def test_no_full_access_permission(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)
    await add_user_to_group(client, user, user2, create_group_response.json()["id"])
    await add_user_to_group(client, user, user3, create_group_response.json()["id"])

    await set_authorization(client, user3)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user2['id']}/{GroupPermission.FULL_ACCESS.value}"
    )
    assert permission_response.status_code == status.HTTP_403_FORBIDDEN


async def test_success_full_access_deleted(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)
    await add_user_to_group(client, user, user2, create_group_response.json()["id"])
    await add_user_to_group(client, user, user3, create_group_response.json()["id"])

    await set_authorization(client, user)
    permission_grant_response = await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user2['id']}/{GroupPermission.FULL_ACCESS.value}"
    )
    assert permission_grant_response.status_code == status.HTTP_201_CREATED

    await set_authorization(client, user)
    permission_response = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user2['id']}/{GroupPermission.FULL_ACCESS.value}"
    )
    assert permission_response.status_code == status.HTTP_200_OK


async def test_success_permission_already_deleted(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    create_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, create_group_response.json()["id"])

    await set_authorization(client, user)
    permission_response_1 = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user2['id']}/{GroupPermission.INVITE_MEMBERS.value}"
    )
    assert permission_response_1.status_code == status.HTTP_200_OK

    permission_response_2 = await client.delete(
        f"{group_router.prefix}/{create_group_response.json()['id']}/members/{user2['id']}/{GroupPermission.INVITE_MEMBERS.value}"
    )
    assert permission_response_2.status_code == status.HTTP_200_OK
