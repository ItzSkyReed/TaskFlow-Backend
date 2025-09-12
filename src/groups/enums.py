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
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GroupPermission(str, Enum):
    INVITE_MEMBERS = "INVITE_MEMBERS"  # Позволяет приглашать участников в группу
    KICK_MEMBERS = "BAN_MEMBERS"  # Позволяет исключать пользователей из группы
    ACCEPT_JOIN_REQUESTS = (
        "ACCEPT_JOIN_REQUESTS"  # Позволяет принимать от участников запросы на вступление в группу
    )
    MANAGE_GROUP = "EDIT_GROUP"  # Позволяет изменять name, avatar, max численность группы
    CONTROL_MEMBERS = (
        "CONTROL_MEMBERS"  # Позволяет изменять права пользователей (кроме MANAGE_MEMBERS, FULL_ACCESS)
    )
    MANAGE_TASKS = "MANAGE_TASKS"  # Позволяет создавать/изменять/удалять задачи
    FULL_ACCESS = "FULL_ACCESS"  # Полный доступ (включая добавление MANAGE_MEMBERS другим пользователям)
