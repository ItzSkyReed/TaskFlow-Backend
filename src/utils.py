import io

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel
from sqlalchemy.orm import Mapped

from .constants import ALLOWED_AVATAR_CONTENT_TYPES, MAX_AVATAR_SIZE
from .database import Base as SQlAlchemyBase
from .exceptions import (
    ExceededAvatarSizeException,
    InvalidAvatarFileException,
    UnsupportedAvatarFormatException,
)


async def update_model_from_schema(
    model: SQlAlchemyBase | Mapped[SQlAlchemyBase], schema: BaseModel
) -> None:
    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)


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

    file.file.seek(0)
