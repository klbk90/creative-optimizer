"""
Redis cache wrapper for UTM tracking system.
"""

import os
from typing import Optional, Any
import json
import redis
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RedisCache:
    """Redis cache wrapper with graceful fallback."""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._connect()

    def _connect(self):
        """Connect to Redis with error handling."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.client.ping()
            logger.info(f"✅ Connected to Redis: {redis_url}")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Continuing without cache.")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default 1 hour)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            serialized = json.dumps(value)
            self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def flush(self) -> bool:
        """
        Flush all cache.

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False


# Global cache instance
_cache_instance = None


def get_redis() -> RedisCache:
    """
    Get global Redis cache instance (singleton).

    Returns:
        RedisCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance
