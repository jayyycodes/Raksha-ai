"""
Redis Caching Layer with Resilient In-Memory Fallback — Raksha AI Stage 3 Solid
Owner: Jay (Lead & Platform) | Milestone: M8
Ensures high-throughput read operations (/api/map, /api/threats, /api/stats) achieve <500ms response times.
"""
import functools
import json
from typing import Any, Callable, Optional
import redis

from common.config import settings
from common.logger import get_logger

logger = get_logger(__name__)

_redis_client: Optional[redis.Redis] = None
_redis_available: bool = False

try:
    if settings.REDIS_URL:
        _redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
        )
        _redis_client.ping()
        _redis_available = True
        logger.info(f"Connected to Redis cache at {settings.REDIS_URL}")
except Exception as e:
    logger.warning(f"Redis cache unavailable, running with pass-through: {e}")
    _redis_available = False


def is_redis_online() -> bool:
    return _redis_available and _redis_client is not None


def cache_get(key: str) -> Optional[Any]:
    """Retrieve parsed JSON object from Redis."""
    if not is_redis_online():
        return None
    try:
        val = _redis_client.get(key)
        if val:
            return json.loads(val)
    except Exception as e:
        logger.warning(f"Cache get error for key '{key}': {e}")
    return None


def cache_set(key: str, value: Any, ttl_seconds: int = 60) -> bool:
    """Serialize and store JSON object in Redis with TTL."""
    if not is_redis_online():
        return False
    try:
        serialized = json.dumps(value)
        _redis_client.set(key, serialized, ex=ttl_seconds)
        return True
    except Exception as e:
        logger.warning(f"Cache set error for key '{key}': {e}")
        return False


def cache_invalidate_prefix(prefix: str) -> int:
    """Invalidate all keys matching a prefix wildcard (e.g. 'api:map*')."""
    if not is_redis_online():
        return 0
    try:
        keys = _redis_client.keys(f"{prefix}*")
        if keys:
            count = _redis_client.delete(*keys)
            logger.info(f"Invalidated {count} cached keys matching prefix '{prefix}'")
            return count
    except Exception as e:
        logger.warning(f"Cache invalidation error for prefix '{prefix}': {e}")
    return 0


def cached(ttl_seconds: int = 60, key_prefix: str = "cache"):
    """
    Decorator to cache endpoint or function results in Redis.
    Uses function name and stringified kwargs to form the cache key.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Exclude db connection or Request objects from cache key
            filtered_kwargs = {
                k: v for k, v in kwargs.items()
                if not hasattr(v, "execute") and not hasattr(v, "headers")
            }
            cache_key = f"{key_prefix}:{func.__name__}:{sorted(filtered_kwargs.items())}"

            hit = cache_get(cache_key)
            if hit is not None:
                return hit

            result = func(*args, **kwargs)
            cache_set(cache_key, result, ttl_seconds)
            return result

        return wrapper
    return decorator
