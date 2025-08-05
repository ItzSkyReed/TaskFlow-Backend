from typing import Final

LOGIN_PATTERN: Final[str] = (
    r"^[a-zA-Z0-9_]+$"  # Паттерн допустимых символов логина пользователя
)
PASSWORD_PATTERN: Final[str] = (
    r"^[A-Za-z\d!@#$%&*]*$"  # Паттерн допустимых символов пароля пользователя
)

MAX_REFRESH_TOKENS: Final[int] = (
    5  # Максимальное количество refresh токенов у 1 пользователя
)
