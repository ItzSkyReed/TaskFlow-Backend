from starlette import status

from src.exceptions import BaseAPIException


class CannotInviteYourselfException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="Cannot invite yourself to the group",
            loc=["groups"],
            err_type="value_error.invite_self",
        )


class CannotUserThatIsAlreadyInThatGroupException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="Cannot invite user that is already in group",
            loc=["groups", "members"],
            err_type="value_error.invited_user_already_in_group",
        )


class GroupWithSuchNameAlreadyExistsException(BaseAPIException):
    def __init__(self, group_name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg=f'Невозможно назвать группу "{group_name}" потому что группа с таким названием уже существует',
            loc=["groups", "body", "name"],
            err_type="value_error.group_name_already_exists",
        )


class TooManyCreatedGroupsException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="Слишком много ранее созданных групп",
            loc=["groups"],
            err_type="value_error.too_many_groups",
        )


class GroupNotFoundException(BaseAPIException):
    """
    404

    Вызывается если группа не найдена
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Группа с таким ID не найдена",
            loc=["body", "group_id"],
            err_type="value_error.invalid_group_id",
        )


class NotEnoughGroupPermissionsException(BaseAPIException):
    """
    403

    Возвращается если недостаточно прав для изменения ресурса
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="У вас нет прав для изменения этой группы",
            loc=["permissions"],
            err_type="permissions_error.forbidden",
        )

class GroupSizeConflictException(BaseAPIException):
    def __init__(self, current_members: int, requested_size: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg=(
                f"Невозможно уменьшить размер группы до {requested_size}, "
                f"поскольку на данный момент в группе находится {current_members} человек"
            ),
            loc=["max_members_count"],
            err_type="group.conflict.too_many_members",
        )