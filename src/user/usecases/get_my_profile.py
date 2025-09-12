from logging import getLogger
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import UserSchema
from ..services import get_user_with_profile

logger = getLogger(__name__)


async def get_my_profile(
    user_id: UUID,
    session: AsyncSession,
) -> UserSchema:
    """
    Получение своего профиля по UUID из access token
    :param user_id: UUID профиля
    :param session: Сессия
    """
    return UserSchema.model_validate(await get_user_with_profile(user_id, session), from_attributes=True)
