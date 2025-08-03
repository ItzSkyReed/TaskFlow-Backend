from starlette import status

from ..exceptions import BaseAPIException


class UserNotFoundByIdentifierException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="user with such identifier is not found",
            loc=["body", "identifier"],
            err_type="value_error.invalid_identifier",
        )

class UserNotFoundByIdException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            msg="user with such id is not found",
            loc=["access_token", "sub"],
            err_type="value_error.invalid_sub",
        )
