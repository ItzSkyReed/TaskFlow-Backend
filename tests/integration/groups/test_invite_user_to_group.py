import uuid

from httpx import AsyncClient
from integration.helpers import add_user_to_group, create_group, register_and_login, set_authorization
from integration.helpers.group import add_permission
from starlette import status

from src.groups import GroupPermission, group_router


async def test_invite_user_success(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    created_group_response = await create_group(client)

    assert created_group_response.status_code == status.HTTP_201_CREATED

    invite_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    assert invite_response.status_code == status.HTTP_201_CREATED


async def test_invite_user_success_full_access(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    created_group_response = await create_group(client)

    await add_user_to_group(client, user, user3, created_group_response.json()["id"])
    await add_permission(
        client, user, user3, created_group_response.json()["id"], GroupPermission.FULL_ACCESS
    )

    await set_authorization(client, user3)
    invite_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    assert invite_response.status_code == status.HTTP_201_CREATED


async def test_invite_user_success_invite_members(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    created_group_response = await create_group(client)

    await add_user_to_group(client, user, user3, created_group_response.json()["id"])
    await add_permission(
        client, user, user3, created_group_response.json()["id"], GroupPermission.INVITE_MEMBERS
    )

    await set_authorization(client, user3)
    invite_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    assert invite_response.status_code == status.HTTP_201_CREATED


async def test_invite_user_invite_yourself(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    created_group_response = await create_group(client)

    assert created_group_response.status_code == status.HTTP_201_CREATED

    invite_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user["id"]},
    )
    assert invite_response.status_code == status.HTTP_400_BAD_REQUEST
    assert invite_response.json()["detail"][0]["type"] == "group.invitation.cannot_invite_yourself"


async def test_invite_user_no_group(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    invite_response = await client.post(
        f"{group_router.prefix}/{uuid.uuid4()}/invitations",
        json={"user_id": user2["id"]},
    )
    assert invite_response.status_code == status.HTTP_404_NOT_FOUND
    assert invite_response.json()["detail"][0]["type"] == "group.not_found"


async def test_invite_user_no_user(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)

    assert created_group_response.status_code == status.HTTP_201_CREATED

    invite_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": str(uuid.uuid4())},
    )
    assert invite_response.status_code == status.HTTP_404_NOT_FOUND
    assert invite_response.json()["detail"][0]["type"] == "user.not_found"


async def test_invite_user_not_found(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)

    assert created_group_response.status_code == status.HTTP_201_CREATED

    invite_response = await client.post(
        f"{group_router.prefix}/{uuid.uuid4()}/invitations",
        json={"user_id": str(uuid.uuid4())},
    )
    assert invite_response.status_code == status.HTTP_404_NOT_FOUND
    assert invite_response.json()["detail"][0]["type"] == "group.not_found"


async def test_invite_user_already_invited(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)

    invite_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    assert invite_response.status_code == status.HTTP_201_CREATED

    invite_response_2 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    assert invite_response_2.status_code == status.HTTP_201_CREATED

    assert invite_response.json()["created_at"] == invite_response_2.json()["created_at"]


async def test_invite_user_already_in_group(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, created_group_response.json()["id"])

    await set_authorization(client, user)
    invite_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    assert invite_response.status_code == status.HTTP_400_BAD_REQUEST
    assert invite_response.json()["detail"][0]["type"] == "group.invitation.invited_user_already_in_group"


async def test_invite_user_no_permissions(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)
    created_group_response = await create_group(client)
    await add_user_to_group(client, user, user2, created_group_response.json()["id"])

    await set_authorization(client, user2)
    invite_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user3["id"]},
    )
    assert invite_response.status_code == status.HTTP_403_FORBIDDEN
