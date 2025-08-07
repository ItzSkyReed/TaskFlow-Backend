import io

from fastapi import File, UploadFile
from PIL import Image, UnidentifiedImageError

from .constants import ALLOWED_AVATAR_CONTENT_TYPES, MAX_AVATAR_SIZE
from .exceptions import (
    ExceededAvatarSizeException,
    InvalidAvatarFileException,
    UnsupportedAvatarFormatException,
)


async def validate_avatar_file(file: UploadFile = File(...)) -> UploadFile:
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

    return file
