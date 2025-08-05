from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import PublicUserSchema
from ..services import get_user_with_profile


async def get_public_user_profile(
    user_id: UUID,
    session: AsyncSession,
) -> PublicUserSchema:
    """
    Получение публичного профиля пользователя
    :param user_id: UUID получаемого профиля
    :param session: Сессия
    """
    return PublicUserSchema.model_validate(
        await get_user_with_profile(user_id, session), from_attributes=True
    )
