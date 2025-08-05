from starlette import status

from ..exceptions import BaseAPIException


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


class InvalidPasswordException(BaseAPIException):
    """
    Вызывается если пароли не совпадают (при входе в аккаунт)
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Incorrect password",
            loc=["body", "password"],
            err_type="value_error.invalid_password",
        )


class InvalidOldPasswordException(BaseAPIException):
    """
    Вызывается если старый пароль не совпадает (при смене пароля)
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Incorrect old password",
            loc=["body", "password"],
            err_type="value_error.invalid_old_password",
        )


class PasswordsAreSameException(BaseAPIException):
    """
    Вызывается если пароли (старый и новый) совпадают при их смене
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="Incorrect old password",
            loc=["body", "password"],
            err_type="value_error.old_password_is_same_as_new",
        )


class TokenExpiredException(BaseAPIException):
    """
    Вызывается при истечении срока валидности токена (как access, так и refresh)
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Token Expired",
            loc=["header", "token"],
            err_type="token_error.token_expired",
        )


class InvalidTokenException(BaseAPIException):
    """
    Вызывается если токен в целом не верен, например был модифицирован или изменен на произвольный
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Token is invalid",
            loc=["header", "token"],
            err_type="token_error.invalid_token",
        )


class RefreshTokenNotFound(BaseAPIException):
    """
    Вызывается если refresh токен не найден в куках
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Refresh token not found in cookies",
            loc=["cookie", "token"],
            err_type="token_error.refresh_token_not_found_in_cookies",
        )


class RefreshTokenNotWhitelisted(BaseAPIException):
    """
    Вызывается если refresh токена с таким jti нет в redis, т.е он не валиден (например смена пароля).
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Refresh token JTI not found in whitelist",
            loc=["cookie", "token"],
            err_type="token_error.refresh_token_not_found_in_whitelist",
        )


class AccessTokenNotFound(BaseAPIException):
    """
    Вызывается если access токен не найден в заголовке, хотя должен был быть
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Access token not found in headers",
            loc=["headers", "token"],
            err_type="token_error.access_token_not_found",
        )
