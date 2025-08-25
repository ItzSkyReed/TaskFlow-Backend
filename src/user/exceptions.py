from starlette import status

from ..exceptions import BaseAPIException


class UserNotFoundByIdentifierException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="user with such identifier is not found",
            loc=["body", "identifier"],
            err_type="value_error.invalid_identifier",
        )


class UserNotFoundByIdException(BaseAPIException):
    """
    404
    """
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="user with such id is not found",
            loc=["access_token", "sub"],
            err_type="value_error.invalid_sub",
        )


class EmailAlreadyInUseException(BaseAPIException):
    """
    409

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
