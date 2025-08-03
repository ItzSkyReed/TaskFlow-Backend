from sqlalchemy.ext.asyncio import AsyncSession

from ...user import User
from ...user.schemas import UserSchema
from ..schemas import TokenSchema, TokenUserSchema, SignUpSchema
from ..services import add_new_refresh_token
from ..utils import JWTUtils, PasswordUtils


async def sign_up_user(
        user_in: SignUpSchema,
        session: AsyncSession,
) -> TokenSchema:
    hashed_password = PasswordUtils.hash_password(user_in.password)
    user = User(
        login=user_in.login,
        email=user_in.email,
        hashed_password=hashed_password,
    )
    session.add(user)

    await session.commit()
    await session.refresh(user)

    # Создание токенов
    access_token = JWTUtils.create_access_token(user.id)
    refresh_token = JWTUtils.create_refresh_token(user.id)

    # Сохраняем refresh_token в БД/Redis
    await add_new_refresh_token(user.id, refresh_token.jti)

    return TokenSchema(
        access_token=access_token, refresh_token=refresh_token.token
    )
