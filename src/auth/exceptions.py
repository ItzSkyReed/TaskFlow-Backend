from starlette import status

from ..exceptions import BaseAPIException


class EmailAlreadyInUseException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg="Email is already in use",
            loc=["body", "email"],
            err_type="value_error.email_in_use",
        )


class LoginAlreadyInUseException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg="Login is already in use",
            loc=["body", "email"],
            err_type="value_error.login_in_use",
        )


class InvalidPasswordException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Incorrect password",
            loc=["body", "password"],
            err_type="value_error.invalid_password",
        )


class InvalidOldPasswordException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Incorrect old password",
            loc=["body", "password"],
            err_type="value_error.invalid_password",
        )


class TokenExpiredException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Token Expired",
            loc=["header", "token"],
            err_type="token_error.token_expired",
        )


class InvalidTokenException(BaseAPIException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Token is invalid",
            loc=["header", "token"],
            err_type="token_error.invalid_token",
        )


class RefreshTokenNotFound(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Refresh token not found in cookies",
            loc=["cookie", "token"],
            err_type="token_error.refresh_token_not_found_in_cookies",
        )


class InvalidRefreshToken(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="Refresh token JTI not found in whitelist",
            loc=["cookie", "token"],
            err_type="token_error.refresh_token_not_found_in_whitelist",
        )


class AccessTokenNotFound(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="Access token not found in headers",
            loc=["headers", "token"],
            err_type="token_error.access_token_not_found",
        )
