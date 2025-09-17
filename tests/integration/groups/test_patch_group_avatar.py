import io

from httpx import AsyncClient
from integration.helpers import (
    create_group,
    get_random_bytes,
    get_random_symbols,
    register_and_login,
    set_authorization,
)
from PIL import Image
from starlette import status

from src.constants import MAX_AVATAR_SIZE
from src.groups import group_router


async def test_patch_group_avatar_success(client: AsyncClient, cdn_client: AsyncClient):
    user = await register_and_login(client)
    await set_authorization(client, user)

    random_symbols = await get_random_symbols()
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
    assert resp.status_code == 200

    image_bytes.seek(0)
    assert image_bytes.read() == resp.content


async def test_patch_group_avatar_no_permission(client: AsyncClient):
    user1 = await register_and_login(client)
    await set_authorization(client, user1)

    random_symbols = await get_random_symbols()
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

    # Отправим с другого аккаунт то же фото (чтобы быть уверенным, что оно валидное)
    user2 = await register_and_login(client)
    await set_authorization(client, user2)

    resp = await client.patch(
        f"{group_router.prefix}/{group_id}/avatar",
        files=files,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


async def test_patch_group_avatar_too_large(client: AsyncClient):
    user1 = await register_and_login(client)
    await set_authorization(client, user1)

    random_symbols = await get_random_symbols()
    group_resp = await create_group(
        client,
        random_symbols,
    )
    group_id = group_resp.json()["id"]

    file = await get_random_bytes(MAX_AVATAR_SIZE + 1)

    files = {
        "file": ("avatar.webp", file, "image/webp"),
    }

    resp = await client.patch(
        f"{group_router.prefix}/{group_id}/avatar",
        files=files,
    )

    assert resp.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE


async def test_patch_group_avatar_invalid_content_type(client: AsyncClient):
    user1 = await register_and_login(client)
    await set_authorization(client, user1)

    random_symbols = await get_random_symbols()
    group_resp = await create_group(
        client,
        random_symbols,
    )
    group_id = group_resp.json()["id"]

    image = Image.new("RGB", (10, 10), color="red")
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="WEBP")  # правильный
    image_bytes.seek(0)

    files = {
        "file": ("avatar.webp", image_bytes, "image/png"),  # неправильный
    }

    resp = await client.patch(
        f"{group_router.prefix}/{group_id}/avatar",
        files=files,
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST


async def test_patch_group_avatar_invalid_webp(client: AsyncClient):
    user1 = await register_and_login(client)
    await set_authorization(client, user1)

    random_symbols = await get_random_symbols()
    group_resp = await create_group(
        client,
        random_symbols,
    )
    group_id = group_resp.json()["id"]

    image = Image.new("RGB", (10, 10), color="red")
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="png")  # неправильный
    image_bytes.seek(0)

    files = {
        "file": ("avatar.webp", image_bytes, "image/webp"),  # правильный
    }

    resp = await client.patch(
        f"{group_router.prefix}/{group_id}/avatar",
        files=files,
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["detail"][0]["type"] == "avatar_error.unsupported_avatar_format"


async def test_patch_group_avatar_invalid_file(client: AsyncClient):
    user1 = await register_and_login(client)
    await set_authorization(client, user1)

    random_symbols = await get_random_symbols()
    group_resp = await create_group(
        client,
        random_symbols,
    )
    group_id = group_resp.json()["id"]

    file = await get_random_bytes(10000)

    files = {
        "file": ("avatar.webp", file, "image/webp"),
    }

    resp = await client.patch(
        f"{group_router.prefix}/{group_id}/avatar",
        files=files,
    )

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert resp.json()["detail"][0]["type"] == "avatar_error.invalid_avatar"


# TODO добавить
