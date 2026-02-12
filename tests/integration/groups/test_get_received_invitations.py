from httpx import AsyncClient
from integration.helpers import add_user_to_group, create_group, register_and_login, set_authorization

from src.groups import InvitationStatus, group_router


async def test_get_received_invitations(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user2)

    invitations_response = await client.get(
        f"{group_router.prefix}/invitations/received",
    )

    assert invitations_response.json() == []

    await set_authorization(client, user)
    created_group_response = await create_group(client)

    await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )

    await set_authorization(client, user2)

    invitations_response = await client.get(
        f"{group_router.prefix}/invitations/received",
    )
    assert invitations_response.json()[0]["group"]["id"] == created_group_response.json()["id"]


async def test_get_received_invitations_pending(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)

    await set_authorization(client, user)
    created_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, created_group_response.json()["id"])

    await set_authorization(client, user2)
    await client.delete(
        f"{group_router.prefix}/{created_group_response.json()['id']}/members/me",
    )
    await set_authorization(client, user)
    await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )

    await set_authorization(client, user2)
    invitations_response = await client.get(
        f"{group_router.prefix}/invitations/received",
        params={"invitation_status": InvitationStatus.PENDING.value},
    )

    assert len(invitations_response.json()) == 1
    assert invitations_response.json()[0]["status"] == InvitationStatus.PENDING.value


async def test_get_received_invitations_accepted(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)

    await set_authorization(client, user)
    created_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, created_group_response.json()["id"])

    await set_authorization(client, user2)
    await client.delete(
        f"{group_router.prefix}/{created_group_response.json()['id']}/members/me",
    )
    await set_authorization(client, user)
    await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )

    await set_authorization(client, user2)
    invitations_response = await client.get(
        f"{group_router.prefix}/invitations/received",
        params={"invitation_status": InvitationStatus.ACCEPTED.value},
    )

    assert len(invitations_response.json()) == 1
    assert invitations_response.json()[0]["status"] == InvitationStatus.ACCEPTED.value


async def test_get_received_invitations_rejected(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)

    await set_authorization(client, user)
    created_group_response = await create_group(client)

    invitation_response = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    await set_authorization(client, user2)
    await client.patch(
        f"{group_router.prefix}/invitations/{invitation_response.json()['id']}",
        json={"response": InvitationStatus.REJECTED.value},
    )

    invitations_response = await client.get(
        f"{group_router.prefix}/invitations/received",
        params={"invitation_status": InvitationStatus.REJECTED.value},
    )

    assert len(invitations_response.json()) == 1
    assert invitations_response.json()[0]["status"] == InvitationStatus.REJECTED.value


async def test_get_received_invitations_limit(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)

    await set_authorization(client, user)
    created_group_response = await create_group(client)

    invitation_response_1 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    await set_authorization(client, user2)
    await client.patch(
        f"{group_router.prefix}/invitations/{invitation_response_1.json()['id']}",
        json={"response": InvitationStatus.REJECTED.value},
    )

    await set_authorization(client, user)
    invitation_response_2 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    await set_authorization(client, user2)
    await client.patch(
        f"{group_router.prefix}/invitations/{invitation_response_2.json()['id']}",
        json={"response": InvitationStatus.REJECTED.value},
    )

    invitations_response = await client.get(
        f"{group_router.prefix}/invitations/received",
        params={"limit": 1},
    )

    assert len(invitations_response.json()) == 1
    ids = [i["id"] for i in invitations_response.json()]
    assert invitation_response_2.json()["id"] in ids


async def test_get_received_invitations_offset(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)

    await set_authorization(client, user)
    created_group_response = await create_group(client)

    invitation_response_1 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    await set_authorization(client, user2)
    await client.patch(
        f"{group_router.prefix}/invitations/{invitation_response_1.json()['id']}",
        json={"response": InvitationStatus.REJECTED.value},
    )

    await set_authorization(client, user)
    invitation_response_2 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    await set_authorization(client, user2)
    await client.patch(
        f"{group_router.prefix}/invitations/{invitation_response_2.json()['id']}",
        json={"response": InvitationStatus.REJECTED.value},
    )

    await set_authorization(client, user)
    invitation_response_3 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    await set_authorization(client, user2)
    await client.patch(
        f"{group_router.prefix}/invitations/{invitation_response_3.json()['id']}",
        json={"response": InvitationStatus.REJECTED.value},
    )

    invitations_response = await client.get(
        f"{group_router.prefix}/invitations/received",
        params={"offset": 1},
    )

    assert len(invitations_response.json()) == 2

    ids = [i["id"] for i in invitations_response.json()]
    assert invitation_response_1.json()["id"] in ids
    assert invitation_response_2.json()["id"] in ids


async def test_get_received_invitations_offset_limit(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)

    await set_authorization(client, user)
    created_group_response = await create_group(client)

    invitation_response_1 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    await set_authorization(client, user2)
    await client.patch(
        f"{group_router.prefix}/invitations/{invitation_response_1.json()['id']}",
        json={"response": InvitationStatus.REJECTED.value},
    )

    await set_authorization(client, user)
    invitation_response_2 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    await set_authorization(client, user2)
    await client.patch(
        f"{group_router.prefix}/invitations/{invitation_response_2.json()['id']}",
        json={"response": InvitationStatus.REJECTED.value},
    )

    await set_authorization(client, user)
    invitation_response_3 = await client.post(
        f"{group_router.prefix}/{created_group_response.json()['id']}/invitations",
        json={"user_id": user2["id"]},
    )
    await set_authorization(client, user2)
    await client.patch(
        f"{group_router.prefix}/invitations/{invitation_response_3.json()['id']}",
        json={"response": InvitationStatus.REJECTED.value},
    )

    invitations_response = await client.get(
        f"{group_router.prefix}/invitations/received",
        params={"offset": 1, "limit": 1},
    )

    assert len(invitations_response.json()) == 1
    # Descending order
    assert invitations_response.json()[0]["id"] == invitation_response_2.json()["id"]
