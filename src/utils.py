from pydantic import BaseModel
from sqlalchemy.orm import Mapped

from .database import Base as SQlAlchemyBase


async def update_model_from_schema(
    model: SQlAlchemyBase | Mapped[SQlAlchemyBase], schema: BaseModel
) -> None:
    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)
