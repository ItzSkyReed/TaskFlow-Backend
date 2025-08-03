from logging import getLogger

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import InvalidOldPasswordException
from ..schemas import ChangePasswordSchema
from ..services import get_user_by_id
from ..services.token_rotation import remove_all_refresh_tokens_except
from ..utils import JWTUtils, PasswordUtils

logger = getLogger(__name__)


async def change_user_password(
    passwords: ChangePasswordSchema,
    refresh_token: str,
    session: AsyncSession,
) -> None:
    refresh_token_payload = JWTUtils.decode_token(refresh_token)
    user = await get_user_by_id(refresh_token_payload.sub, session)

    if not PasswordUtils.verify_password(user.hashed_password, passwords.old_password):
        raise InvalidOldPasswordException()

    new_hashed_password = PasswordUtils.hash_password(passwords.new_password)

    user.hashed_password = new_hashed_password
    await session.commit()

    await remove_all_refresh_tokens_except(
        user_id=refresh_token_payload.sub,
        except_token_jti=refresh_token_payload.jti,
    )
