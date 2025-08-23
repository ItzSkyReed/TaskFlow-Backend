# Импорт всех моделей для корректной работы миграций и самих моделей

from .groups import Group, GroupInvitation, GroupMember, InvitationStatus, GroupPermission, GroupUserPermission, GroupJoinRequest  # noqa: F401
from .user import User, UserProfile  # noqa: F401
