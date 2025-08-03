import time
from uuid import UUID

from ...redis.client import redis_client
from ..config import get_auth_settings
from ..constants import MAX_REFRESH_TOKENS

auth_settings = get_auth_settings()


async def add_new_refresh_token(user_id: UUID, token_jti: UUID) -> None:
    key = f"refresh:{user_id}"

    async with redis_client.lock(f"lock:refresh_tokens:{user_id}", timeout=5):
        pipe = redis_client.pipeline()
        pipe.zadd(key, {str(token_jti): int(time.time())})
        pipe.zcard(key)
        pipe.expire(key, auth_settings.refresh_token_expires_in)

        results = await pipe.execute()
        _, count, _ = results

        if count > MAX_REFRESH_TOKENS:
            remove_count = count - MAX_REFRESH_TOKENS
            await redis_client.zremrangebyrank(key, 0, remove_count - 1)


async def remove_all_refresh_tokens_except(
    user_id: UUID, except_token_jti: UUID
) -> None:
    lock_key = f"lock:change_password:{user_id}"
    async with redis_client.lock(lock_key, timeout=5):
        key = f"refresh:{user_id}"
        pipe = redis_client.pipeline()

        pipe.zrange(key, 0, -1)
        results = await pipe.execute()
        all_tokens = results[0]

        tokens_to_remove = [
            token for token in all_tokens if token != str(except_token_jti)
        ]
        if tokens_to_remove:
            pipe.zrem(key, *tokens_to_remove)
            await pipe.execute()


async def remove_previous_refresh_token(user_id: UUID, token_jti: UUID) -> None:
    key = f"refresh:{user_id}"
    await redis_client.zrem(key, str(token_jti))


async def remove_all_refresh_tokens(user_id: UUID) -> None:
    key = f"refresh:{user_id}"
    await redis_client.delete(key)


async def is_refresh_jti_valid(user_id: UUID, jti: UUID) -> bool:
    key = f"refresh:{user_id}"
    score = await redis_client.zscore(key, str(jti))
    return score is not None
