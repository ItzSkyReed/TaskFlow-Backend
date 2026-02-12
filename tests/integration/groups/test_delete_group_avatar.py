import io

from httpx import AsyncClient
from integration.helpers import (
    add_user_to_group,
    create_group,
    get_random_symbols,
    register_and_login,
    set_authorization,
)
from integration.helpers.group import add_permission
from PIL import Image
from starlette import status

from src.groups import GroupPermission, group_router


async def test_delete_group_avatar_success(client: AsyncClient, cdn_client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = get_random_symbols()
    group_resp = await create_group(
        client,
        random_symbols,
    )
    group_id = group_resp.json()["id"]

    image = Image.new("RGB", (10, 10), color="red")
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="WEBP")
    image_bytes.seek(0)

    files = {
        "file": ("avatar.webp", image_bytes, "image/webp"),
    }

    resp = await client.patch(
        f"{group_router.prefix}/{group_id}/avatar",
        files=files,
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["id"] == group_id
    assert data["name"] == random_symbols
    assert data["avatar_url"] == f"/task_flow/cdn/avatars/groups/{group_id}.webp"

    resp = await cdn_client.get(f"/avatars/groups/{group_id}.webp")
    assert resp.status_code == status.HTTP_200_OK

    image_bytes.seek(0)
    assert image_bytes.read() == resp.content

    resp = await client.delete(f"{group_router.prefix}/{group_id}/avatar")
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    resp = await cdn_client.get(f"/avatars/groups/{group_id}.webp")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_group_avatar_no_permission(client: AsyncClient, cdn_client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = get_random_symbols()
    group_resp = await create_group(
        client,
        random_symbols,
    )
    group_id = group_resp.json()["id"]

    image = Image.new("RGB", (10, 10), color="red")
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="WEBP")
    image_bytes.seek(0)

    files = {
        "file": ("avatar.webp", image_bytes, "image/webp"),
    }

    resp = await client.patch(
        f"{group_router.prefix}/{group_id}/avatar",
        files=files,
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["id"] == group_id
    assert data["name"] == random_symbols
    assert data["avatar_url"] == f"/task_flow/cdn/avatars/groups/{group_id}.webp"

    resp = await cdn_client.get(f"/avatars/groups/{group_id}.webp")
    assert resp.status_code == status.HTTP_200_OK

    image_bytes.seek(0)
    assert image_bytes.read() == resp.content

    await set_authorization(client, user2)
    resp = await client.delete(f"{group_router.prefix}/{group_id}/avatar")
    assert resp.status_code == status.HTTP_403_FORBIDDEN

    resp = await cdn_client.get(f"/avatars/groups/{group_id}.webp")
    assert resp.status_code == status.HTTP_200_OK


async def test_delete_group_avatar_full_access(client: AsyncClient, cdn_client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = get_random_symbols()
    group_resp = await create_group(
        client,
        random_symbols,
    )
    await add_user_to_group(client, user, user2, group_resp.json()["id"])
    await add_permission(client, user, user2, group_resp.json()["id"], GroupPermission.FULL_ACCESS)

    await set_authorization(client, user)
    group_id = group_resp.json()["id"]

    image = Image.new("RGB", (10, 10), color="red")
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="WEBP")
    image_bytes.seek(0)

    files = {
        "file": ("avatar.webp", image_bytes, "image/webp"),
    }

    resp = await client.patch(
        f"{group_router.prefix}/{group_id}/avatar",
        files=files,
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["id"] == group_id
    assert data["name"] == random_symbols
    assert data["avatar_url"] == f"/task_flow/cdn/avatars/groups/{group_id}.webp"

    resp = await cdn_client.get(f"/avatars/groups/{group_id}.webp")
    assert resp.status_code == status.HTTP_200_OK

    image_bytes.seek(0)
    assert image_bytes.read() == resp.content

    await set_authorization(client, user2)
    resp = await client.delete(f"{group_router.prefix}/{group_id}/avatar")
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    resp = await cdn_client.get(f"/avatars/groups/{group_id}.webp")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_group_avatar_manage_group(client: AsyncClient, cdn_client: AsyncClient):
    user = await register_and_login(client)
    user2 = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = get_random_symbols()
    group_resp = await create_group(
        client,
        random_symbols,
    )
    await add_user_to_group(client, user, user2, group_resp.json()["id"])
    await add_permission(client, user, user2, group_resp.json()["id"], GroupPermission.MANAGE_GROUP)

    await set_authorization(client, user)
    group_id = group_resp.json()["id"]

    image = Image.new("RGB", (10, 10), color="red")
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="WEBP")
    image_bytes.seek(0)

    files = {
        "file": ("avatar.webp", image_bytes, "image/webp"),
    }

    resp = await client.patch(
        f"{group_router.prefix}/{group_id}/avatar",
        files=files,
    )

    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["id"] == group_id
    assert data["name"] == random_symbols
    assert data["avatar_url"] == f"/task_flow/cdn/avatars/groups/{group_id}.webp"

    resp = await cdn_client.get(f"/avatars/groups/{group_id}.webp")
    assert resp.status_code == status.HTTP_200_OK

    image_bytes.seek(0)
    assert image_bytes.read() == resp.content

    await set_authorization(client, user2)
    resp = await client.delete(f"{group_router.prefix}/{group_id}/avatar")
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    resp = await cdn_client.get(f"/avatars/groups/{group_id}.webp")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
