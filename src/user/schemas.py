from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..auth.constants import LOGIN_PATTERN


class UserSchema(BaseModel):
    id: UUID
    login: str = Field(
        ..., min_length=4, max_length=64, pattern=LOGIN_PATTERN, examples=["srun4ikPRO"]
    )
    email: EmailStr = Field(..., max_length=320, examples=["johndoe@example.com"])

    model_config = ConfigDict(from_attributes=True)
