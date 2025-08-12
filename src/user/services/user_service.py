import io
from uuid import UUID

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, joinedload

from ...user import User, UserNotFoundByIdentifierException, UserNotFoundByIdException
from ..constants import ALLOWED_AVATAR_CONTENT_TYPES, MAX_AVATAR_SIZE
from ..exceptions import (
    EmailAlreadyInUseException,
    ExceededAvatarSizeException,
    InvalidAvatarFileException,
    LoginAlreadyInUseException,
    UnsupportedAvatarFormatException,
)


async def get_user_by_identifier(identifier: str, session: AsyncSession) -> User:
    """
    Получение пользователя по identifier
    :param identifier: Login/Email пользователя
    :param session: Сессия
    :raises UserNotFoundByIdentifierException: Если пользователь не найден
    """
    user = (
        await session.execute(
            select(User).where(or_(User.email == identifier, User.login == identifier))
        )
    ).scalar_one_or_none()
    if not user:
        raise UserNotFoundByIdentifierException()
    return user


async def get_user(user_id: UUID, session: AsyncSession) -> User:
    """
    Получение пользователя по identifier
    :param user_id: UUID пользователя
    :param session: Сессия
    :raises UserNotFoundByIdException: Если пользователь не найден
    """
    user = (
        await session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if user is None:
        raise UserNotFoundByIdException()
    return user


async def get_user_with_profile(user_id: UUID, session: AsyncSession) -> User:
    """
    Получение пользователя с загруженным UserProfile
    :param user_id: Id пользователя
    :param session: Сессия
    :raises UserNotFoundByIdException: Если пользователь не найден
    """
    user = (
        await session.execute(
            select(User)
            .options(joinedload(User.user_profile))
            .filter(User.id == user_id)
        )
    ).scalar_one_or_none()
    if user is None:
        raise UserNotFoundByIdException()
    return user


async def user_exists_by_field(
    field: InstrumentedAttribute,
    value: str,
    session: AsyncSession,
) -> bool:
    """
    Проверяет, существует ли уже пользователь с совпадающем значением в определенным полем
    :param session: Сессия
    :param field: Поле модели
    :param value: Значение поля
    """
    result = await session.execute(select(User).where(field == value))
    return result.scalar_one_or_none() is not None


async def check_email_unique(email: EmailStr, session: AsyncSession) -> None:
    """
    Проверяет уникален ли Email.
    :param email: Email пользователя
    :param session: Сессия
    :raises LoginAlreadyInUseException: Если такой email уже используется
    """
    if await user_exists_by_field(User.email, email, session):
        raise EmailAlreadyInUseException()


async def check_login_unique(login: str, session: AsyncSession) -> None:
    """
    Проверяет уникален ли Login.
    :param login: Login пользователя
    :param session: Сессия
    :raises LoginAlreadyInUseException: Если такой login уже используется
    """
    if await user_exists_by_field(User.login, login, session):
        raise LoginAlreadyInUseException()


async def validate_avatar_file(file: UploadFile) -> None:
    # Проверка по заголовкам
    if file.size and file.size > MAX_AVATAR_SIZE:
        raise ExceededAvatarSizeException()
    if file.content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
        raise UnsupportedAvatarFormatException()

    try:
        content = await file.read()
    except Exception as err:
        raise InvalidAvatarFileException() from err

    if len(content) > MAX_AVATAR_SIZE:
        raise ExceededAvatarSizeException()

    try:
        image = Image.open(io.BytesIO(content))
        if image.format != "WEBP":
            raise UnsupportedAvatarFormatException()
    except UnidentifiedImageError as err:
        raise InvalidAvatarFileException() from err

    # Возвращаемся к началу файла
    file.file.seek(0)
