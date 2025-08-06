from fastapi import UploadFile, File

from .constants import MAX_AVATAR_SIZE, ALLOWED_AVATAR_CONTENT_TYPES
from .exceptions import ExceededAvatarSizeException, InvalidAvatarFileException, UnsupportedAvatarFormatException
from PIL import Image, UnidentifiedImageError
import io

async def validate_avatar_file(file: UploadFile = File(...)) -> UploadFile:
    # Проверка по заголовкам
    if file.size > MAX_AVATAR_SIZE:
        raise ExceededAvatarSizeException()
    if file.content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
        raise UnsupportedAvatarFormatException()

    try:
        content = await file.read()
    except Exception:
        raise InvalidAvatarFileException()

    if len(content) > MAX_AVATAR_SIZE:
        raise ExceededAvatarSizeException()

    try:
        image = Image.open(io.BytesIO(content))
        if image.format != "WEBP":
            raise UnsupportedAvatarFormatException()
    except UnidentifiedImageError:
        raise InvalidAvatarFileException()

    # Возвращаемся к началу файла
    file.file.seek(0)

    return file