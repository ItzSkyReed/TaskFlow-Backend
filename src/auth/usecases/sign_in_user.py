from sqlalchemy.ext.asyncio import AsyncSession

from ...user.schemas import UserSchema
from ..exceptions import InvalidPasswordException
from ..schemas import TokenSchema, TokenUserSchema, SignInSchema
from ..services import add_new_refresh_token, get_user_by_identifier
from ..utils import JWTUtils, PasswordUtils


async def sign_in_user(
    user_in: SignInSchema,
    session: AsyncSession,
) -> TokenSchema:
    user = await get_user_by_identifier(user_in.identifier, session)

    if not PasswordUtils.verify_password(user.hashed_password, user_in.password):
        raise InvalidPasswordException()

    access_token = JWTUtils.create_access_token(user.id)
    refresh_token = JWTUtils.create_refresh_token(user.id)

    await add_new_refresh_token(user_id=user.id, token_jti=refresh_token.jti)

    return TokenSchema(
            access_token=access_token, refresh_token=refresh_token.token
        )
