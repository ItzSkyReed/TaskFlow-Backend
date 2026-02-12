# Импорт всех моделей для корректной работы миграций и самих моделей

from .groups import (  # noqa: F401
    Group,
    GroupInvitation,
    GroupJoinRequest,
    GroupMember,
    GroupPermission,
    GroupUserPermission,
    InvitationStatus,
    JoinRequestStatus,
)
from .user import User, UserProfile  # noqa: F401
