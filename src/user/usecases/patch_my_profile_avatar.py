from logging import getLogger
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...minio import AVATARS_BUCKET_NAME, get_minio_client
from ...utils import validate_avatar_file
from ..schemas import UserSchema
from ..services import get_user_with_profile


async def patch_my_profile_avatar(
    file: UploadFile,
    user_id: UUID,
    session: AsyncSession,
) -> UserSchema:
    """
    Обновление аватарки профиля пользователя (себя)
    :param file: Содержит данные о самом аватаре пользователя
    :param user_id: UUID профиля
    :param session: Сессия
    """
    await validate_avatar_file(file)

    user = await get_user_with_profile(user_id, session)

    async with get_minio_client() as client:
        await client.put_object(
            Bucket=AVATARS_BUCKET_NAME,
            Key=f"users/{user_id}.webp",
            Body=await file.read(),
            ContentType=file.content_type,
        )

    user.has_avatar = True
    session.add(user)
    await session.commit()

    return UserSchema.model_validate(user, from_attributes=True)
