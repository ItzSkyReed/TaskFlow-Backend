from typing import Final

NAME_PATTERN: Final[str] = r"^[\p{L}\d\s'_-]+$"

MAX_AVATAR_SIZE: Final[int] = 3 * 1024 * 1024

ALLOWED_AVATAR_CONTENT_TYPES: Final[frozenset[str]] = frozenset({"image/webp"})