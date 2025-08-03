from redis.asyncio import Redis

from .. import get_settings

settings = get_settings()


redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    username=settings.redis_user,
    password=settings.redis_password,
    decode_responses=True,
)
