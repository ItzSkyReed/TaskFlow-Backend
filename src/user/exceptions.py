from starlette import status

from ..exceptions import BaseAPIException
from .constants import MAX_AVATAR_SIZE


class UserNotFoundByIdentifierException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="user with such identifier is not found",
            loc=["body", "identifier"],
            err_type="value_error.invalid_identifier",
        )


class UserNotFoundByIdException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="user with such id is not found",
            loc=["access_token", "sub"],
            err_type="value_error.invalid_sub",
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


class EmailAlreadyInUseException(BaseAPIException):
    """
    Вызывается если Email уже используется у какого-либо пользователя
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg="Email is already in use",
            loc=["body", "email"],
            err_type="value_error.email_in_use",
        )


class LoginAlreadyInUseException(BaseAPIException):
    """
    Вызывается если Login уже используется у какого-либо пользователя
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg="Login is already in use",
            loc=["body", "email"],
            err_type="value_error.login_in_use",
        )
