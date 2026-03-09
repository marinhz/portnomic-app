import json
import logging
from typing import Any

from app.redis_client import redis_client

logger = logging.getLogger("shipflow")

DEFAULT_TTL = 300  # 5 minutes


async def cache_get(key: str) -> Any | None:
    """Get value from cache, return None on miss."""
    try:
        raw = await redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.warning("Cache get failed for key=%s", key, exc_info=True)
        return None


async def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Set value in cache with TTL."""
    try:
        await redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        logger.warning("Cache set failed for key=%s", key, exc_info=True)


async def cache_delete(key: str) -> None:
    """Delete a cache entry."""
    try:
        await redis_client.delete(key)
    except Exception:
        logger.warning("Cache delete failed for key=%s", key, exc_info=True)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching pattern (e.g. 'tenant:{id}:ports:*')."""
    try:
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                await redis_client.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        logger.warning("Cache delete pattern failed for pattern=%s", pattern, exc_info=True)


def make_cache_key(tenant_id: str, resource: str, *args: str) -> str:
    """Build a namespaced cache key: tenant:{tid}:{resource}:{args}"""
    parts = [f"tenant:{tenant_id}", resource]
    parts.extend(args)
    return ":".join(parts)
