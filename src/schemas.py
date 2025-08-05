from typing import Annotated

from pydantic import BaseModel, Field


class SuccessResponseModel(BaseModel):
    """
    Используется для отправки успешного ответа в 200 коде в случае отсутствия каких либо других схем
    """

    success: Annotated[bool, Field(default=True, frozen=True)] = True
