from typing import Annotated

from pydantic import BaseModel, Field


class ErrorItem(BaseModel):
    """
    Поля, используемые в ошибках
    """

    msg: Annotated[str, Field(..., description="Текст ошибки")]
    type: Annotated[
        str, Field(..., description="Тип ошибки (value_error, type_error и т.д.)")
    ]
    loc: Annotated[
        None | list[str],
        Field(
            default=None,
            description='Местоположение ошибки (["body", "field_name", ...])',
        ),
    ]
    ctx: Annotated[
        dict[str, str | int | float] | None,
        Field(default=None, description="Контекст ошибки (доп. параметры валидатора)"),
    ]


class ErrorResponseModel(BaseModel):
    detail: Annotated[
        list[ErrorItem], Field(..., description="Список ошибок (даже если она одна)")
    ]


class SuccessResponseModel(BaseModel):
    """
    Используется для отправки успешного ответа в 200 коде в случае отсутствия каких либо других схем
    """

    success: Annotated[bool, Field(default=True, frozen=True)] = True
