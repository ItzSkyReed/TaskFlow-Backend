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


class GroupNotFoundByIdException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="group with such id is not found",
            loc=["body", "group_id"],
            err_type="value_error.invalid_group_id",
        )


class NotEnoughPermissionsException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="You don't have permissions to change avatar of that group",
            loc=["permissions"],
            err_type="permissions_error.forbidden",
        )
