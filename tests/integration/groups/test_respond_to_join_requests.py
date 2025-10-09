import uuid

from httpx import AsyncClient
from integration.helpers import add_user_to_group, create_group, register_and_login, set_authorization
from integration.helpers.group import add_permission
from starlette import status

from src.groups import GroupPermission, JoinRequestStatus, group_router


async def test_no_join_request_found(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    join_response = await client.patch(
        f"{group_router.prefix}/join-requests/{str(uuid.uuid4())}",
        json={"response": JoinRequestStatus.ACCEPTED},
    )
    assert join_response.status_code == status.HTTP_404_NOT_FOUND


async def test_group_is_full(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)
    group_response = await create_group(client, max_members_count=2)

    await set_authorization(client, user2)
    user2_send_join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )

    assert user2_send_join_response.status_code == status.HTTP_200_OK

    await add_user_to_group(client, user, user3, group_response.json()["id"])

    await set_authorization(client, user)
    user2_respond_join_response = await client.patch(
        f"{group_router.prefix}/join-requests/{user2_send_join_response.json()['id']}",
        json={"response": JoinRequestStatus.ACCEPTED},
    )

    assert user2_respond_join_response.status_code == status.HTTP_409_CONFLICT
    assert user2_respond_join_response.json()["detail"][0]["type"] == "group.conflict.group_is_full"


async def test_no_permissions(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)
    group_response = await create_group(client)

    await set_authorization(client, user2)
    user2_send_join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )

    assert user2_send_join_response.status_code == status.HTTP_200_OK

    await add_user_to_group(client, user, user3, group_response.json()["id"])

    await set_authorization(client, user3)
    user2_respond_join_response = await client.patch(
        f"{group_router.prefix}/join-requests/{user2_send_join_response.json()['id']}",
        json={"response": JoinRequestStatus.ACCEPTED},
    )

    assert user2_respond_join_response.status_code == status.HTTP_403_FORBIDDEN


async def test_success_rejected_response(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    group_response = await create_group(client)

    await set_authorization(client, user2)
    user2_send_join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )

    assert user2_send_join_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user)
    user2_respond_join_response = await client.patch(
        f"{group_router.prefix}/join-requests/{user2_send_join_response.json()['id']}",
        json={"response": JoinRequestStatus.REJECTED},
    )

    assert user2_respond_join_response.status_code == status.HTTP_200_OK
    assert user2_respond_join_response.json()["status"] == JoinRequestStatus.REJECTED.value


async def test_success_accepted_response(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    group_response = await create_group(client)

    await set_authorization(client, user2)
    user2_send_join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )

    assert user2_send_join_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user)
    user2_respond_join_response = await client.patch(
        f"{group_router.prefix}/join-requests/{user2_send_join_response.json()['id']}",
        json={"response": JoinRequestStatus.ACCEPTED},
    )

    assert user2_respond_join_response.status_code == status.HTTP_200_OK
    assert user2_respond_join_response.json()["status"] == JoinRequestStatus.ACCEPTED.value


async def test_success_accepted_response_full_access(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)

    await set_authorization(client, user)
    group_response = await create_group(client)

    await add_user_to_group(client, user, user2, group_response.json()["id"])
    await add_permission(client, user, user2, group_response.json()["id"], GroupPermission.FULL_ACCESS)

    await set_authorization(client, user3)
    user3_send_join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )

    assert user3_send_join_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user2)
    user2_respond_join_response = await client.patch(
        f"{group_router.prefix}/join-requests/{user3_send_join_response.json()['id']}",
        json={"response": JoinRequestStatus.ACCEPTED},
    )

    assert user2_respond_join_response.status_code == status.HTTP_200_OK
    assert user2_respond_join_response.json()["status"] == JoinRequestStatus.ACCEPTED.value


async def test_success_accepted_response_accept_join_requests(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)

    await set_authorization(client, user)
    group_response = await create_group(client)

    await add_user_to_group(client, user, user2, group_response.json()["id"])
    await add_permission(
        client, user, user2, group_response.json()["id"], GroupPermission.ACCEPT_JOIN_REQUESTS
    )

    await set_authorization(client, user3)
    user3_send_join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )

    assert user3_send_join_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user2)
    user2_respond_join_response = await client.patch(
        f"{group_router.prefix}/join-requests/{user3_send_join_response.json()['id']}",
        json={"response": JoinRequestStatus.ACCEPTED},
    )

    assert user2_respond_join_response.status_code == status.HTTP_200_OK
    assert user2_respond_join_response.json()["status"] == JoinRequestStatus.ACCEPTED.value


async def test_join_request_already_resolved(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)
    group_response = await create_group(client)

    await set_authorization(client, user2)
    user2_send_join_response = await client.post(
        f"{group_router.prefix}/{group_response.json()['id']}/join-requests",
    )

    assert user2_send_join_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user)
    user2_respond_join_response = await client.patch(
        f"{group_router.prefix}/join-requests/{user2_send_join_response.json()['id']}",
        json={"response": JoinRequestStatus.REJECTED},
    )

    assert user2_respond_join_response.status_code == status.HTTP_200_OK

    user2_second_respond_join_response = await client.patch(
        f"{group_router.prefix}/join-requests/{user2_send_join_response.json()['id']}",
        json={"response": JoinRequestStatus.REJECTED},
    )
    assert user2_second_respond_join_response.status_code == status.HTTP_409_CONFLICT
    assert (
        user2_second_respond_join_response.json()["detail"][0]["type"]
        == "group.conflict.join_request_already_resolved"
    )
