import uuid

import pytest
from httpx import AsyncClient
from integration.helpers import add_user_to_group, create_group, register_and_login, set_authorization
from starlette import status

from src.groups import group_router


@pytest.mark.order(
    after=[
        "test_respond_to_invitation.py::test_invitation_members_limit",
        "test_invite_user_to_group.py::test_invite_user_no_permissions",
    ]
)
async def test_change_group_creator_change_to_yourself(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)
    change_response = await client.patch(
        f"{group_router.prefix}/{created_group_response.json()['id']}/creator",
        json={"new_creator_id": user["id"]},
    )
    assert change_response.status_code == status.HTTP_400_BAD_REQUEST
    assert change_response.json()["detail"][0]["type"] == "group.cannot_change_creator_to_yourself"


@pytest.mark.order(
    after=[
        "test_respond_to_invitation.py::test_invitation_members_limit",
        "test_invite_user_to_group.py::test_invite_user_no_permissions",
    ]
)
async def test_change_group_creator_not_creator(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)
    await add_user_to_group(client, user, user2, created_group_response.json()["id"])
    await add_user_to_group(client, user, user3, created_group_response.json()["id"])

    await set_authorization(client, user2)
    change_response = await client.patch(
        f"{group_router.prefix}/{created_group_response.json()['id']}/creator",
        json={"new_creator_id": user3["id"]},
    )
    assert change_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.order(
    after=[
        "test_respond_to_invitation.py::test_invitation_members_limit",
        "test_invite_user_to_group.py::test_invite_user_no_permissions",
    ]
)
async def test_change_group_creator_new_creator_is_not_in_group(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)

    change_response = await client.patch(
        f"{group_router.prefix}/{created_group_response.json()['id']}/creator",
        json={"new_creator_id": user2["id"]},
    )
    assert change_response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.order(
    after=[
        "test_respond_to_invitation.py::test_invitation_members_limit",
        "test_invite_user_to_group.py::test_invite_user_no_permissions",
    ]
)
async def test_change_group_creator_user_not_found(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)

    change_response = await client.patch(
        f"{group_router.prefix}/{created_group_response.json()['id']}/creator",
        json={"new_creator_id": str(uuid.uuid4())},
    )
    assert change_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.order(
    after=[
        "test_respond_to_invitation.py::test_invitation_members_limit",
        "test_invite_user_to_group.py::test_invite_user_no_permissions",
    ]
)
async def test_change_group_creator_success(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)
    await add_user_to_group(client, user, user2, created_group_response.json()["id"])

    await set_authorization(client, user)
    change_response = await client.patch(
        f"{group_router.prefix}/{created_group_response.json()['id']}/creator",
        json={"new_creator_id": user2["id"]},
    )
    assert change_response.status_code == status.HTTP_200_OK

    group = await client.get(
        f"{group_router.prefix}/{created_group_response.json()['id']}",
    )
    assert group.json()["creator_id"] == user2["id"]
