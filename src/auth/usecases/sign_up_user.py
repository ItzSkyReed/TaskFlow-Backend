from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ...user import User, UserProfile
from ...user.exceptions import EmailAlreadyInUseException, LoginAlreadyInUseException
from ..schemas import SignUpSchema, TokenSchema
from ..services import add_new_refresh_token
from ..utils import JWTUtils, PasswordUtils


async def sign_up_user(
    user_in: SignUpSchema,
    session: AsyncSession,
) -> TokenSchema:
    """
    Логика регистрации пользователя
    :param user_in: Схема регистрации пользователя
    :param session: Сессия
    :return: Схема содержащая access и refresh токены
    """
    hashed_password = PasswordUtils.hash_password(user_in.password)

    user = User(
        login=user_in.login,
        email=user_in.email,
        hashed_password=hashed_password,
    )

    try:
        session.add(user)
        await session.flush()

    except IntegrityError as err:
        await session.rollback()
        if getattr(err.orig, "pgcode", None) == "23505":
            # asyncpg UniqueViolationError
            uq_err = err.orig.__cause__  # ty: ignore[possibly-unbound-attribute]
            if uq_err.constraint_name == "ix_users_email": # ty: ignore[unresolved-attribute]
                raise EmailAlreadyInUseException() from err
            elif uq_err.constraint_name == "ix_users_login": # ty: ignore[unresolved-attribute]
                raise LoginAlreadyInUseException() from err
            raise
        raise  # pragma: no cover

    user_profile = UserProfile(id=user.id, name=user_in.name or user_in.login)
    session.add(user_profile)

    await session.commit()

    # Создание токенов
    access_token = JWTUtils.create_access_token(user.id)
    refresh_token = JWTUtils.create_refresh_token(user.id)

    # Сохраняем refresh_token в БД/Redis
    await add_new_refresh_token(user.id, refresh_token.jti)

    return TokenSchema(access_token=access_token, refresh_token=refresh_token.token)
