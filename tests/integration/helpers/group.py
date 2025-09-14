from httpx import AsyncClient, Response
from integration.helpers import get_random_symbols

from src.groups import group_router


async def create_group(
    client: AsyncClient,
    name: str = get_random_symbols(),
    description: str | None = None,
    max_members_count: int | None = 100,
    invitations: list[str] | None = None,
) -> Response:
    """Создание группы и возврат её uuid"""

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
