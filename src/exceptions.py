# Global exceptions
from math import ceil

from fastapi import HTTPException
from starlette import status
from starlette.requests import Request
from starlette.responses import Response


class BaseAPIException(HTTPException):
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


async def rate_limit_default_callback(
    request: Request, response: Response, pexpire: int
):
    expire = ceil(pexpire / 1000)
    raise RateLimitExceeded(headers={"Retry-After": str(expire)})


class RateLimitExceeded(BaseAPIException):
    def __init__(
        self,
        msg: str = "Too Many Requests - rate limit exceeded",
        loc: list[str] | None = None,
        err_type: str = "rate_limit.exceeded",
        **kwargs,
    ):
        if loc is None:
            loc = ["header", "Retry-After"]
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            msg=msg,
            loc=loc,
            err_type=err_type,
            **kwargs,
        )
