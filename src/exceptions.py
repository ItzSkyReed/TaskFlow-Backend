# Global exceptions

from fastapi import HTTPException
from starlette import status

from .constants import MAX_AVATAR_SIZE


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


class SomethingWentWrongException(BaseAPIException):
    def __init__(self):
        """
        500

        Вызывается если неясно, что пошло не так.
        """
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="Something went wrong",
            err_type="internal_server_error",
        )


class ExceededAvatarSizeException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            msg=f"Max avatar size is {MAX_AVATAR_SIZE} bytes",
            loc=["body", "avatar"],
            err_type="avatar_error.avatar_too_large",
        )


class InvalidAvatarFileException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="user with such id is not found",
            loc=["body", "avatar"],
            err_type="avatar_error.invalid_avatar",
        )


class UnsupportedAvatarFormatException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="only WebP photos are allowed",
            loc=["body", "avatar"],
            err_type="avatar_error.invalid_avatar",
        )
