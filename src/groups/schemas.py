from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field

from ..config import get_settings
from ..user.schemas import PublicUserSchema
from .constants import NAME_PATTERN
from .enums import InvitationStatus

settings = get_settings()


class GroupAvatarMixin(BaseModel):
    has_avatar: Annotated[bool, Field(default=False, exclude=True)]

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        if getattr(self, "has_avatar", False):
            return f"{settings.cdn_path}/avatars/groups/{self.id}.webp"
        return None


class CreateGroupSchema(BaseModel):
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, max_length=50, min_length=6),
        Field(
            ...,
            pattern=NAME_PATTERN,
            description="Публичное название группы",
            examples=["MegaGroup", "НевероятнаяГруппа123"],
        ),
    ]

    description: Annotated[
        str | None,
        StringConstraints(
            strip_whitespace=True,
            max_length=2000,
        ),
        Field(
            default=None,
            description="Публичное название группы",
            examples=["MegaGroup", "НевероятнаяГруппа123"],
        ),
    ]

    max_members_count: Annotated[
        int, Field(ge=2, le=100, default=100, serialization_alias="max_members")
    ]

    invitations: Annotated[
        list[UUID] | None,
        Field(
            default=None,
            description="Приглашения участников (приглашения будут отосланы сразу после создания)",
        ),
    ]


class GroupSummarySchema(GroupAvatarMixin, BaseModel):
    id: UUID

    name: Annotated[str, Field(max_length=50)]

    creator_id: UUID

    created_at: Annotated[datetime, Field(...)]

    max_members_count: Annotated[int, Field(..., validation_alias="max_members")]

    model_config = ConfigDict(from_attributes=True)


class GroupSearchSchema(GroupAvatarMixin, BaseModel):
    id: UUID

    name: Annotated[str, Field(max_length=50)]

    max_members_count: Annotated[int, Field(..., validation_alias="max_members")]

    model_config = ConfigDict(from_attributes=True)


class GroupDetailSchema(GroupAvatarMixin, BaseModel):
    id: UUID

    name: Annotated[str, Field(max_length=50)]

    description: Annotated[
        str | None,
        Field(default=None),
    ]

    creator_id: UUID

    created_at: Annotated[datetime, Field(...)]

    max_members_count: Annotated[int, Field(..., validation_alias="max_members")]

    members: Annotated[list["GroupMemberSchema"], Field(...)]

    model_config = ConfigDict(from_attributes=True)


class GroupMemberSchema(BaseModel):
    user: Annotated[PublicUserSchema, Field(...)]

    joined_at: Annotated[datetime, Field(...)]

    permissions: Annotated[list[str] | None, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class InviteUserToGroupSchema(BaseModel):
    user_id: UUID


class InvitationSummarySchema(BaseModel):
    id: Annotated[UUID, Field(...)]
    group_id: Annotated[UUID, Field(...)]
    inviter_id: Annotated[UUID, Field(...)]
    invitee_id: Annotated[UUID, Field(...)]
    status: Annotated[InvitationStatus, Field(...)]
    created_at: Annotated[datetime, Field(...)]
    updated_at: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)


class ReceivedInvitationSchema(BaseModel):
    id: Annotated[UUID, Field(...)]
    group: Annotated[GroupSummarySchema, Field(...)]
    inviter: Annotated[PublicUserSchema, Field(...)]
    status: Annotated[InvitationStatus, Field(...)]
    created_at: Annotated[datetime, Field(...)]
    updated_at: Annotated[datetime, Field(...)]

    model_config = ConfigDict(from_attributes=True)
