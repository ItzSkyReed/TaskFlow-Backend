import uuid

from httpx import AsyncClient
from integration.helpers import add_user_to_group, create_group, register_and_login, set_authorization
from starlette import status

from src.groups import group_router


async def test_leave_from_group_success(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)
    await add_user_to_group(client, user, user2, created_group_response.json()["id"])

    await set_authorization(client, user2)
    leave_response = await client.delete(
        f"{group_router.prefix}/{created_group_response.json()['id']}/members/me",
    )
    assert leave_response.status_code == status.HTTP_204_NO_CONTENT


async def test_leave_from_group_no_group(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    leave_response = await client.delete(
        f"{group_router.prefix}/{str(uuid.uuid4())}/members/me",
    )
    assert leave_response.status_code == status.HTTP_404_NOT_FOUND


async def test_leave_from_group_user_not_in_group(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)

    await set_authorization(client, user2)
    leave_response = await client.delete(
        f"{group_router.prefix}/{created_group_response.json()['id']}/members/me",
    )
    assert leave_response.status_code == status.HTTP_400_BAD_REQUEST


async def test_leave_from_group_creator_cant_leave(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)

    leave_response = await client.delete(
        f"{group_router.prefix}/{created_group_response.json()['id']}/members/me",
    )
    assert leave_response.status_code == status.HTTP_409_CONFLICT
