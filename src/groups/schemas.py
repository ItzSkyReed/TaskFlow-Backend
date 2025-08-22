from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from ..config import get_settings
from ..user.schemas import PublicUserSchema
from .constants import NAME_PATTERN

settings = get_settings()


class CreateGroupSchema(BaseModel):
    name: Annotated[
        str,
        Field(
            ...,
            pattern=NAME_PATTERN,
            min_length=6,
            max_length=50,
            description="Публичное название группы",
            examples=["MegaGroup", "НевероятнаяГруппа123"]
        ),
    ]
    invitations: Annotated[
        list[UUID] | None,
        Field(
            default=None,
            description="Приглашения участников (приглашения будут отосланы сразу после создания)",
        ),
    ]

class GroupSummarySchema(BaseModel):
    id: UUID

    name: Annotated[str, Field(max_length=50)]

    has_avatar: Annotated[bool, Field(default=False, exclude=True)]

    creator_id: UUID

    created_at: Annotated[datetime, Field(...)]

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        # Проверяем наличие атрибута has_avatar и что он True
        if getattr(self, "has_avatar", False):
            return f"{settings.cdn_path}/avatars/groups/{self.id}.webp"
        return None

    model_config = ConfigDict(from_attributes=True)

class GroupDetailSchema(BaseModel):
    id: UUID

    name: Annotated[str, Field(max_length=50)]

    has_avatar: Annotated[bool, Field(default=False, exclude=True)]

    creator_id: UUID

    created_at: Annotated[datetime, Field(...)]

    members: Annotated[list["GroupMemberSchema"], Field(...)]

    @computed_field
    @property
    def avatar_url(self) -> str | None:
        # Проверяем наличие атрибута has_avatar и что он True
        if getattr(self, "has_avatar", False):
            return f"{settings.cdn_path}/avatars/groups/{self.id}.webp"
        return None

    model_config = ConfigDict(from_attributes=True)


class GroupMemberSchema(BaseModel):
    user: Annotated[PublicUserSchema, Field(...)]

    joined_at: Annotated[datetime, Field(...)]

    permissions: Annotated[list[str] | None, Field(...)]

    model_config = ConfigDict(from_attributes=True)
