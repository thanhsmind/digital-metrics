import json
import logging
from typing import Any, Optional, Protocol

from prometheus_client import CollectorRegistry, Counter, Histogram
from redis import Redis

logger = logging.getLogger(__name__)


class CacheMetrics:
    """Cache metrics collector."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize cache metrics with optional registry.

        Args:
            registry: Optional Prometheus registry to use for metrics
        """
        self.hits = Counter(
            "cache_hits_total", "Total number of cache hits", registry=registry
        )
        self.misses = Counter(
            "cache_misses_total",
            "Total number of cache misses",
            registry=registry,
        )
        self.errors = Counter(
            "cache_errors_total",
            "Total number of cache errors",
            registry=registry,
        )
        self.response_time = Histogram(
            "cache_response_seconds",
            "Cache operation response time",
            registry=registry,
        )

    def increment_hits(self):
        """Increment cache hits counter."""
        self.hits.inc()

    def increment_misses(self):
        """Increment cache misses counter."""
        self.misses.inc()


class CacheService(Protocol):
    """Abstract interface for caching service."""

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        pass

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    async def clear(self) -> bool:
        """Clear all cache."""
        pass


class RedisCacheService(CacheService):
    """Redis implementation of cache service."""

    def __init__(self, redis: Redis):
        self.redis = redis
        self.metrics = CacheMetrics()

    async def get(self, key: str) -> Optional[Any]:
        try:
            if value := await self.redis.get(key):
                self.metrics.increment_hits()
                return json.loads(value)
            self.metrics.increment_misses()
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.metrics.errors.inc()
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        try:
            serialized = json.dumps(value)
            return await self.redis.set(key, serialized, ex=ttl)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            self.metrics.errors.inc()
            return False

    async def delete(self, key: str) -> bool:
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            self.metrics.errors.inc()
            return False

    async def clear(self) -> bool:
        try:
            return bool(await self.redis.flushdb())
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            self.metrics.errors.inc()
            return False
