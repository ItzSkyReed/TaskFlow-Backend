from typing import Annotated

from pydantic import BaseModel, Field


class SuccessResponseModel(BaseModel):
    success: Annotated[bool, Field(default=True, frozen=True)]
