import uuid

from httpx import AsyncClient
from integration.helpers import add_user_to_group, create_group, register_and_login, set_authorization
from integration.helpers.group import add_permission
from starlette import status

from src.groups import GroupPermission, JoinRequestStatus, group_router


async def test_group_not_found(client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    join_requests_response = await client.get(
        f"{group_router.prefix}/{str(uuid.uuid4())}/join-requests",
    )

    assert join_requests_response.status_code == status.HTTP_404_NOT_FOUND


async def test_no_permissions(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await add_user_to_group(client, user, user2, create_group_response.json()["id"])

    await set_authorization(client, user2)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    assert join_requests_response.status_code == status.HTTP_403_FORBIDDEN


async def test_success(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    assert join_requests_response.json() == []
    assert join_requests_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user2)
    send_join_response = await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )
    assert send_join_response.json()["id"] == join_requests_response.json()[0]["id"]
    assert send_join_response.status_code == status.HTTP_200_OK


async def test_success_full_access(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)
    await add_user_to_group(client, user, user3, create_group_response.json()["id"])
    await add_permission(client, user, user3, create_group_response.json()["id"], GroupPermission.FULL_ACCESS)

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    assert join_requests_response.json() == []
    assert join_requests_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user2)
    send_join_response = await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    await set_authorization(client, user3)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )
    assert send_join_response.json()["id"] == join_requests_response.json()[0]["id"]
    assert send_join_response.status_code == status.HTTP_200_OK


async def test_success_accept_join_requests(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)
    await add_user_to_group(client, user, user3, create_group_response.json()["id"])
    await add_permission(
        client, user, user3, create_group_response.json()["id"], GroupPermission.ACCEPT_JOIN_REQUESTS
    )

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    assert join_requests_response.json() == []
    assert join_requests_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user2)
    send_join_response = await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    await set_authorization(client, user3)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )
    assert send_join_response.json()["id"] == join_requests_response.json()[0]["id"]
    assert send_join_response.status_code == status.HTTP_200_OK


async def test_limit(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    assert join_requests_response.json() == []
    assert join_requests_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user2)
    await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    await set_authorization(client, user3)
    send_join_response_2 = await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
        params={"limit": 1},
    )
    assert len(join_requests_response.json()) == 1
    assert send_join_response_2.json()["id"] == join_requests_response.json()[0]["id"]
    assert join_requests_response.status_code == status.HTTP_200_OK


async def test_offset(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    assert join_requests_response.json() == []
    assert join_requests_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user2)
    send_join_response = await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    await set_authorization(client, user3)
    await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
        params={"offset": 1},
    )
    assert len(join_requests_response.json()) == 1
    assert send_join_response.json()["id"] == join_requests_response.json()[0]["id"]
    assert join_requests_response.status_code == status.HTTP_200_OK


async def test_offset_limit(client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    user3 = await register_and_login(client)
    user4 = await register_and_login(client)
    await set_authorization(client, user)

    create_group_response = await create_group(client)

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    assert join_requests_response.json() == []
    assert join_requests_response.status_code == status.HTTP_200_OK

    await set_authorization(client, user2)
    send_join_response_1 = await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )
    assert send_join_response_1.status_code == status.HTTP_200_OK

    await set_authorization(client, user3)
    send_join_response_2 = await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )
    assert send_join_response_2.status_code == status.HTTP_200_OK

    await set_authorization(client, user4)
    send_join_response_3 = await client.post(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
    )

    assert send_join_response_3.status_code == status.HTTP_200_OK

    await set_authorization(client, user)
    join_requests_response = await client.get(
        f"{group_router.prefix}/{create_group_response.json()['id']}/join-requests",
        params={"offset": 1, "limit": 1},
    )
    assert len(join_requests_response.json()) == 1
    assert send_join_response_2.json()["id"] == join_requests_response.json()[0]["id"]
    assert join_requests_response.status_code == status.HTTP_200_OK


async def test_filter_by_status(client: AsyncClient):
    owner = await register_and_login(client)
    user1 = await register_and_login(client)
    user2 = await register_and_login(client)

    await set_authorization(client, owner)
    group_response = await create_group(client)
    group_id = group_response.json()["id"]

    await set_authorization(client, user1)
    join_req_1 = await client.post(f"{group_router.prefix}/{group_id}/join-requests")
    assert join_req_1.status_code == status.HTTP_200_OK

    await set_authorization(client, user2)
    join_req_2 = await client.post(f"{group_router.prefix}/{group_id}/join-requests")
    assert join_req_2.status_code == status.HTTP_200_OK

    await set_authorization(client, owner)
    reject_response = await client.patch(
        f"{group_router.prefix}/join-requests/{join_req_1.json()['id']}",
        json={"response": JoinRequestStatus.REJECTED.value},
    )
    assert reject_response.status_code == status.HTTP_200_OK

    rejected_list = await client.get(
        f"{group_router.prefix}/{group_id}/join-requests",
        params={"request_status": [JoinRequestStatus.REJECTED.value]},
    )
    assert rejected_list.status_code == status.HTTP_200_OK

    assert all(r["status"] == JoinRequestStatus.REJECTED for r in rejected_list.json())
    assert len(rejected_list.json()) == 1

    pending_list = await client.get(
        f"{group_router.prefix}/{group_id}/join-requests",
        params={"request_status": [JoinRequestStatus.PENDING.value]},
    )
    assert pending_list.status_code == status.HTTP_200_OK
    assert all(r["status"] == JoinRequestStatus.PENDING.value for r in pending_list.json())
    assert len(pending_list.json()) == 1
