import re
from typing import Final

LOGIN_PATTERN: Final[re.Pattern] = re.compile(r"^[a-zA-Z0-9_]+$")
PASSWORD_PATTERN: Final[re.Pattern] = re.compile(r"^[A-Za-z\d\W_]*$")

MAX_REFRESH_TOKENS: Final[int] = 5
