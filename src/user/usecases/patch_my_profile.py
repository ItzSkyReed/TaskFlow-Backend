from logging import getLogger
from uuid import UUID

from asyncpg import UniqueViolationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ...utils import update_model_from_schema
from ..exceptions import EmailAlreadyInUseException
from ..schemas import PatchUserSchema, UserSchema
from ..services import check_email_unique, get_user_with_profile

async def patch_my_profile(
    patch_schema: PatchUserSchema,
    user_id: UUID,
    session: AsyncSession,
) -> UserSchema:
    """
    Обновление своего профиля
    :param patch_schema: Схема обновления профиля
    :param user_id: UUID профиля
    :param session: Сессия
    """
    user = await get_user_with_profile(user_id, session)

    if patch_schema.email is not None:
        await check_email_unique(patch_schema.email, session)
        user.email = patch_schema.email

    if patch_schema.profile is not None:
        await update_model_from_schema(user.user_profile, patch_schema.profile)

    try:
        await session.commit()
        await session.refresh(user, attribute_names=["user_profile"])
    except IntegrityError as err:
        await session.rollback()

        if isinstance(err.orig, UniqueViolationError):
            raise EmailAlreadyInUseException() from err
        raise

    return UserSchema.model_validate(user, from_attributes=True)
