from typing import Final

MAX_AVATAR_SIZE: Final[int] = 3 * 1024 * 1024

USER_LOGIN_PATTERN: Final[str] = r"^[a-zA-Z0-9_]+$"

USER_NAME_PATTERN: Final[str] = r"^[\p{L}\d\s'_-]+$"

ALLOWED_AVATAR_CONTENT_TYPES: Final[frozenset[str]] = frozenset({"image/webp"})
