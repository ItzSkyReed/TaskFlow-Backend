import uuid

import pytest
from httpx import AsyncClient
from integration.helpers import add_user_to_group, create_group, register_and_login, set_authorization
from starlette import status

from src.groups import group_router


@pytest.mark.order(after="test_create_group.py::test_create_group_unauthorized")
async def test_no_group_found(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    join_response = await client.post(
        f"{group_router.prefix}/{str(uuid.uuid4())}/join-requests",
    )
    assert join_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.order(after="test_respond_to_invitation.py::test_invitation_members_limit")
async def test_user_already_in_group_group_creator(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    group_response = await create_group(client)

    join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )
    assert join_response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.order(after="test_respond_to_invitation.py::test_invitation_members_limit")
async def test_user_already_in_group_group_member(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    group_response = await create_group(client)

    await add_user_to_group(client, user, user2, group_response.json()["id"])

    await set_authorization(client, user2)
    join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )
    assert join_response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.order(after="test_respond_to_invitation.py::test_invitation_members_limit")
async def test_group_is_full(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    group_response = await create_group(client, max_members_count=2)

    await add_user_to_group(client, user, user2, group_response.json()["id"])

    await set_authorization(client, user3)
    join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )
    assert join_response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.order(after="test_respond_to_invitation.py::test_invitation_members_limit")
async def test_join_requests_already_sent(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    group_response = await create_group(client)

    await set_authorization(client, user2)
    join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )
    assert join_response.status_code == status.HTTP_200_OK
    assert group_response.json()["id"] == join_response.json()["group"]["id"]

    join_response_2 = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )
    assert join_response.status_code == status.HTTP_200_OK
    assert join_response_2.json()["id"] == join_response.json()["id"]
    assert join_response_2.json()["created_at"] == join_response.json()["created_at"]


@pytest.mark.order(after="test_respond_to_invitation.py::test_invitation_members_limit")
async def test_join_requests_success(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    group_response = await create_group(client)

    await set_authorization(client, user2)
    join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )
    assert join_response.status_code == status.HTTP_200_OK
    assert group_response.json()["id"] == join_response.json()["group"]["id"]
