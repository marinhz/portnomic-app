import redis.asyncio as aioredis

from app.config import settings

redis_pool = aioredis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=20,
    decode_responses=True,
    socket_timeout=settings.redis_socket_timeout,
    socket_connect_timeout=settings.redis_socket_connect_timeout,
    retry_on_timeout=True,
)

redis_client = aioredis.Redis(connection_pool=redis_pool)


async def get_redis() -> aioredis.Redis:
    return redis_client
