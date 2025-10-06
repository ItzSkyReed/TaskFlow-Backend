from enum import Enum


class InvitationStatus(str, Enum):
    """
    Статусы заявок приглашений
    """

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class JoinRequestStatus(str, Enum):
    """
    Статусы ответов на входящие заявки
    """

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class GroupPermission(str, Enum):
    INVITE_MEMBERS = "INVITE_MEMBERS"  # Позволяет приглашать участников в группу
    ACCEPT_JOIN_REQUESTS = (
        "ACCEPT_JOIN_REQUESTS"  # Позволяет принимать от участников запросы на вступление в группу
    )
    MANAGE_GROUP = "MANAGE_GROUP"  # Позволяет изменять name, avatar, max численность группы
    MANAGE_TASKS = "MANAGE_TASKS"  # Позволяет создавать/изменять/удалять задачи
    FULL_ACCESS = "FULL_ACCESS"  # Полный доступ
