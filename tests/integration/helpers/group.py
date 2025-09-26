from uuid import UUID

from httpx import AsyncClient, Response
from integration.helpers import get_random_symbols
from integration.helpers.user import AuthResult, set_authorization
from starlette import status

from src.groups import group_router


async def create_group(
    client: AsyncClient,
    name: str | None = None,
    description: str | None = None,
    max_members_count: int | None = 100,
    invitations: list[str] | None = None,
) -> Response:
    """Создание группы и возврат её uuid"""
    if not name:
        name = await get_random_symbols()

    payload = {
        "name": name,
        "description": description,
        "max_members_count": max_members_count,
        "invitations": invitations,
    }

    response = await client.post(
        f"{group_router.prefix}",
        json=payload,
    )

    return response


async def add_user_to_group(
    client: AsyncClient, group_creator: AuthResult, user_to_add: AuthResult, group_id: UUID
):
    await set_authorization(client, group_creator)
    invite_response = await client.post(
        f"{group_router.prefix}/{group_id}/invitations",
        json={"user_id": user_to_add["id"]},
    )

    assert invite_response.status_code == status.HTTP_201_CREATED

    await set_authorization(client, user_to_add)
    user_to_add_accept_invite_response = await client.patch(
        f"{group_router.prefix}/invitations/{invite_response.json()['id']}",
        json={"response": "ACCEPTED"},
    )
    assert user_to_add_accept_invite_response.status_code == status.HTTP_200_OK
