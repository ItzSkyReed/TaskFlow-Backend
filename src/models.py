# Импорт всех моделей для корректной работы миграций и самих моделей

from .groups import Group, GroupInvitation, GroupMembers, InvitationStatus  # noqa: F401
from .user import User, UserProfile  # noqa: F401
