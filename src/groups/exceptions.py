from starlette import status

from src.exceptions import BaseAPIException


class TooManyCreatedGroupsException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="User is a creator of too many groups",
            loc=["groups"],
            err_type="value_error.too_many_groups",
        )
