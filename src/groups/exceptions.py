from uuid import UUID

from starlette import status

from ..exceptions import BaseAPIException


class CannotInviteYourselfException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="Cannot invite yourself to the group",
            loc=["groups"],
            err_type="group.invitation.cannot_invite_yourself",
        )


class CannotInviteUserThatIsAlreadyInThatGroupException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="Cannot invite user that is already in group",
            loc=["groups", "members"],
            err_type="group.invitation.invited_user_already_in_group",
        )


class GroupWithSuchNameAlreadyExistsException(BaseAPIException):
    """
    409

    Вызывается при попытке создать группу или изменить название группы на уже существующее
    """

    def __init__(self, group_name: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg=f'Невозможно назвать группу "{group_name}" потому что группа с таким названием уже существует',
            loc=["groups", "body", "name"],
            err_type="group.conflict.group_name_already_exists",
        )


class TooManyCreatedGroupsException(BaseAPIException):
    """
    403

    Возвращается если у пользователя создано слишком много групп
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg="Слишком много ранее созданных групп",
            loc=["groups"],
            err_type="group.conflict.too_many_groups_created",
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
            err_type="group.not_found",
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
            err_type="group.permissions.forbidden",
        )


class GroupSizeConflictException(BaseAPIException):
    """
    409

    Вызывается если пользователь пытается уменьшить размер группы до такого, что участников в ней должно быть меньше, чем есть сейчас.
    """

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


class CannotKickYourselfException(BaseAPIException):
    """
    400

    Возвращается если пользователь пытается исключить сам себя из группы
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="Нельзя исключить самого себя из группы",
            loc=["group", "user_id"],
            err_type="group.cannot_kick_self",
        )


class CannotChangeCreatorToYourselfException(BaseAPIException):
    """
    400

    Возвращается если пользователь пытается самому себе передать создателя группы
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg="Нельзя самому себе передать создателя группы",
            loc=["group", "user_id"],
            err_type="group.cannot_change_creator_to_yourself",
        )


class RequiredUserNotInGroupException(BaseAPIException):
    """
    400

    Возвращается если пользователь не состоит в группе, хотя это требуется запросом
    """

    def __init__(self, user_id: UUID):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            msg=f"Пользователь {user_id} не состоит в требуемой группе",
            loc=["group", "user_id"],
            err_type="group.required_user_not_in_group",
        )


class CannotKickGroupCreatorException(BaseAPIException):
    """
    403

    Возвращается если пользователь пытается исключить создателя группы
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            msg="Нельзя исключить создателя группы из неё",
            loc=["group", "creator_id"],
            err_type="group.cannot_kick_creator",
        )


class CreatorCantLeaveFromGroupException(BaseAPIException):
    """
    409

    Возвращается если пользователь, являющий создателем группы пытается выйти из нее
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg="Нельзя будучи создателем группы выйти из нее",
            loc=["group", "creator_id"],
            err_type="group.conflict.creator_cant_leave_from_group",
        )


class GroupInvitationNotFoundException(BaseAPIException):
    """
    404

    Возвращается если приглашение пользователя не найдено
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            msg="Приглашение в группу не найдено",
            loc=["group", "user_id"],
            err_type="group.invitation.not_found",
        )


class GroupIsFullException(BaseAPIException):
    """
    409

    Возвращается если невозможно вступить в группу при принятие приглашения т.к группе макс. кол-во пользователей
    """

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            msg="Приглашение в группу не принято, т.к в ней нет свободных мест",
            loc=["group", "members"],
            err_type="group.conflict.group_is_full",
        )
