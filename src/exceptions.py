# Global exceptions
from math import ceil

from fastapi import HTTPException
from starlette import status
from starlette.requests import Request
from starlette.responses import Response


class BaseAPIException(HTTPException):
    """
    Базовая HTTP ошибка, от которой должны наследоваться все остальные
    """

    def __init__(
        self,
        msg: str,
        status_code: int,
        loc: list[str] | None = None,
        err_type: str = "value_error",
        **kwargs,
    ):
        detail: dict[str, str | list[str]] = {"msg": msg, "type": err_type}
        if loc is not None:
            detail["loc"] = loc
        super().__init__(status_code=status_code, detail=[detail], **kwargs)
