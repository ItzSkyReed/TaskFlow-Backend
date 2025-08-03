from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...user import User
from ...user.exceptions import UserNotFoundByIdentifierException


async def get_user_by_identifier(identifier: str, session: AsyncSession) -> User:
    result = await session.execute(
        select(User).where(or_(User.email == identifier, User.login == identifier))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundByIdentifierException()
    return user


async def get_user_by_id(user_id: UUID, session: AsyncSession) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundByIdentifierException()
    return user
