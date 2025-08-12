from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...minio import AVATARS_BUCKET_NAME, get_minio_client
from ..services import get_user_with_profile


async def delete_my_profile_avatar(
    user_id: UUID,
    session: AsyncSession,
):
    """
    Удаление аватарки профиля пользователя (себя)
    :param user_id: UUID профиля
    :param session: Сессия
    """

    user = await get_user_with_profile(user_id, session)

    async with get_minio_client() as client:
        await client.delete_object(
            Bucket=AVATARS_BUCKET_NAME, Key=f"users/{user_id}.webp"
        )

    user.has_avatar = False
    session.add(user)
    await session.commit()
