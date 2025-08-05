import re
from typing import Final

LOGIN_PATTERN: Final[re.Pattern] = re.compile(
    r"^[a-zA-Z0-9_]+$"
)  # Паттерн допустимых символов логина пользователя
PASSWORD_PATTERN: Final[re.Pattern] = re.compile(
    r"^[A-Za-z\d!@#$%&*]*$"
)  # Паттерн допустимых символов пароля пользователя

MAX_REFRESH_TOKENS: Final[int] = (
    5  # Максимальное количество refresh токенов у 1 пользователя
)
