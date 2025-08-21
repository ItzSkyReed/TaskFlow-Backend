from typing import Final

MAX_AVATAR_SIZE: Final[int] = 3 * 1024 * 1024

ALLOWED_AVATAR_CONTENT_TYPES: Final[frozenset[str]] = frozenset({"image/webp"})
