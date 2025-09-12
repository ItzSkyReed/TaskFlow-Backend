import time
from uuid import UUID

from ...redis.client import redis_client
from ..config import get_auth_settings
from ..constants import MAX_REFRESH_TOKENS

auth_settings = get_auth_settings()


async def add_new_refresh_token(user_id: UUID, token_jti: UUID) -> None:
    """
    Добавляет новый refresh токен пользователю, удаляет самый старый если токенов > 5
    :param user_id: UUID пользователя
    :param token_jti: UUID токена который будет сохранен
    """
    key = f"refresh:{user_id}"

    async with redis_client.lock(f"lock:refresh_tokens:{user_id}", timeout=5):
        pipe = redis_client.pipeline()
        pipe.zadd(key, {str(token_jti): int(time.time())})
        pipe.zcard(key)
        pipe.expire(key, auth_settings.refresh_token_expires_in * 60)

        results = await pipe.execute()
        count = results[1]

        if count > MAX_REFRESH_TOKENS:
            remove_count = count - MAX_REFRESH_TOKENS
            await redis_client.zremrangebyrank(key, 0, remove_count - 1)


async def remove_all_refresh_tokens_except(user_id: UUID, except_token_jti: UUID) -> None:
    """
    Удаляет refresh token пользователя кроме определенного
    :param user_id: UUID пользователя
    :param except_token_jti: UUID токена который будет сохранен
    """
    lock_key = f"lock:change_password:{user_id}"
    async with redis_client.lock(lock_key, timeout=5):
        key = f"refresh:{user_id}"
        pipe = redis_client.pipeline()

        pipe.zrange(key, 0, -1)
        results = await pipe.execute()
        all_tokens = results[0]

        tokens_to_remove = [token for token in all_tokens if token != str(except_token_jti)]
        if tokens_to_remove:
            pipe.zrem(key, *tokens_to_remove)
            await pipe.execute()


async def remove_refresh_token(user_id: UUID, token_jti: UUID) -> None:
    """
    Удаляет refresh token пользователя по его jti
    :param user_id: UUID пользователя
    :param token_jti: UUID токена
    """
    await redis_client.zrem(f"refresh:{user_id}", str(token_jti))


async def remove_all_refresh_tokens(user_id: UUID) -> None:
    """
    Удаляет ВСЕ refresh токены пользователя
    :param user_id: UUID пользователя
    """
    await redis_client.delete(f"refresh:{user_id}")


async def is_refresh_jti_valid(user_id: UUID, jti: UUID) -> bool:
    """
    Проверяет, есть ли refresh токен в списке валидных
    :param user_id:
    :param jti:
    :return:
    """
    score = await redis_client.zscore(f"refresh:{user_id}", str(jti))
    return score is not None
