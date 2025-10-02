import uuid

from httpx import AsyncClient
from integration.helpers import create_group, register_and_login, set_authorization
from starlette import status

from src.groups import group_router


async def test_invitation_not_found(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    invite_response = await client.patch(
        f"{group_router.prefix}/invitations/{uuid.uuid4()}",
        json={"response": "ACCEPTED"},
    )
    assert invite_response.status_code == status.HTTP_404_NOT_FOUND


async def test_invitation_success_accept(client: AsyncClient):
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

    await set_authorization(client, user2)
    accept_invite_response = await client.patch(
        f"{group_router.prefix}/invitations/{invite_response.json()['id']}",
        json={"response": "ACCEPTED"},
    )
    assert accept_invite_response.status_code == status.HTTP_200_OK

    group_data = await client.get(f"{group_router.prefix}/{created_group_response.json()['id']}")

    assert user2["id"] in [member["user"]["id"] for member in group_data.json()["members"]]


async def test_invitation_success_rejected(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    created_group_response = await create_group(client, max_members_count=2)

    assert created_group_response.status_code == status.HTTP_201_CREATED

    invite_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    assert invite_response.status_code == status.HTTP_201_CREATED

    await set_authorization(client, user2)
    user2_accept_invite_response = await client.patch(
        f"{group_router.prefix}/invitations/{invite_response.json()['id']}",
        json={"response": "REJECTED"},
    )
    assert user2_accept_invite_response.status_code == status.HTTP_200_OK

    group_data = await client.get(f"{group_router.prefix}/{created_group_response.json()['id']}")

    assert user2["id"] not in [member["user"]["id"] for member in group_data.json()["members"]]


async def test_invitation_members_limit(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    created_group_response = await create_group(client, max_members_count=2)

    assert created_group_response.status_code == status.HTTP_201_CREATED

    invite_response_1 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )

    assert invite_response_1.status_code == status.HTTP_201_CREATED

    invite_response_2 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user3["id"]},
    )

    assert invite_response_2.status_code == status.HTTP_201_CREATED

    await set_authorization(client, user2)
    user2_accept_invite_response = await client.patch(
        f"{group_router.prefix}/invitations/{invite_response_1.json()['id']}",
        json={"response": "ACCEPTED"},
    )
    assert user2_accept_invite_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user3)
    user3_accept_invite_response = await client.patch(
        f"{group_router.prefix}/invitations/{invite_response_2.json()['id']}",
        json={"response": "ACCEPTED"},
    )
    assert user3_accept_invite_response.status_code == status.HTTP_409_CONFLICT
