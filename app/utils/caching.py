"""Caching utilities cho Digital Metrics API."""

import hashlib
import json
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from fastapi import Depends, Request
from redis import Redis

from app.utils.logging import get_logger

logger = get_logger("caching")


class Cache:
    """
    Base class cho các cache implementations.
    """

    def get(self, key: str) -> Optional[Any]:
        """
        Get value từ cache.

        Args:
            key: Cache key

        Returns:
            Cached value hoặc None nếu không có
        """
        raise NotImplementedError("Subclasses must implement get()")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value vào cache.

        Args:
            key: Cache key
            value: Value cần cache
            ttl: Time to live (seconds)
        """
        raise NotImplementedError("Subclasses must implement set()")

    def delete(self, key: str) -> None:
        """
        Xóa key từ cache.

        Args:
            key: Cache key
        """
        raise NotImplementedError("Subclasses must implement delete()")

    def clear(self) -> None:
        """Clear entire cache."""
        raise NotImplementedError("Subclasses must implement clear()")


class InMemoryCache(Cache):
    """
    Simple in-memory cache implementation, phù hợp cho development
    hoặc ứng dụng nhỏ.
    """

    def __init__(self):
        """Initialize empty cache storage."""
        self.cache: Dict[str, Tuple[Any, Optional[datetime]]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value từ cache.

        Args:
            key: Cache key

        Returns:
            Cached value hoặc None nếu không có hoặc đã hết hạn
        """
        if key not in self.cache:
            return None

        value, expiry = self.cache[key]

        # Check expiry
        if expiry is not None and expiry < datetime.now():
            self.delete(key)
            return None

        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value vào cache.

        Args:
            key: Cache key
            value: Value cần cache
            ttl: Time to live (seconds)
        """
        expiry = None
        if ttl is not None:
            expiry = datetime.now() + timedelta(seconds=ttl)

        self.cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """
        Xóa key từ cache.

        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear entire cache."""
        self.cache.clear()


class RedisCache(Cache):
    """
    Redis-based cache implementation, phù hợp cho production.
    """

    def __init__(self, redis_client: Redis, prefix: str = "digital_metrics:"):
        """
        Initialize Redis cache.

        Args:
            redis_client: Redis client
            prefix: Prefix cho cache keys
        """
        self.redis = redis_client
        self.prefix = prefix

    def _build_key(self, key: str) -> str:
        """
        Build full Redis key với prefix.

        Args:
            key: Original key

        Returns:
            Full prefixed key
        """
        return f"{self.prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value từ Redis cache.

        Args:
            key: Cache key

        Returns:
            Cached value hoặc None nếu không có
        """
        full_key = self._build_key(key)
        cached_data = self.redis.get(full_key)

        if cached_data is None:
            return None

        try:
            return pickle.loads(cached_data)
        except Exception as e:
            logger.error(f"Error deserializing cached data: {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value vào Redis cache.

        Args:
            key: Cache key
            value: Value cần cache
            ttl: Time to live (seconds)
        """
        full_key = self._build_key(key)

        try:
            serialized_value = pickle.dumps(value)
            if ttl is not None:
                self.redis.setex(full_key, ttl, serialized_value)
            else:
                self.redis.set(full_key, serialized_value)
        except Exception as e:
            logger.error(f"Error serializing data for cache: {str(e)}")

    def delete(self, key: str) -> None:
        """
        Xóa key từ Redis cache.

        Args:
            key: Cache key
        """
        full_key = self._build_key(key)
        self.redis.delete(full_key)

    def clear(self) -> None:
        """Clear all keys with prefix from Redis."""
        cursor = "0"
        pattern = f"{self.prefix}*"

        while cursor != 0:
            cursor, keys = self.redis.scan(cursor=cursor, match=pattern)
            if keys:
                self.redis.delete(*keys)


# Utilities và decorators


def generate_cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """
    Generate cache key dựa trên args và kwargs.

    Args:
        prefix: Prefix cho cache key
        *args: Positional args
        **kwargs: Keyword args

    Returns:
        Cache key string

    Examples:
        >>> generate_cache_key("metrics", "facebook", date_range="2023-01-01_2023-01-31")
        'metrics:facebook:date_range=2023-01-01_2023-01-31'
    """
    # Convert args and kwargs thành string để hash
    key_parts = [prefix]

    if args:
        key_parts.extend([str(arg) for arg in args])

    if kwargs:
        # Sort để đảm bảo cache keys giống nhau cho cùng kwargs
        sorted_items = sorted(kwargs.items())
        key_parts.extend([f"{k}={v}" for k, v in sorted_items])

    return ":".join(key_parts)


def hash_cache_key(key: str) -> str:
    """
    Hash cache key nếu nó quá dài.

    Args:
        key: Original cache key

    Returns:
        Hashed cache key

    Examples:
        >>> len(hash_cache_key("very_long_key" * 100)) < 100
        True
    """
    if len(key) < 100:  # Redis keys nên ngắn
        return key

    hash_obj = hashlib.md5(key.encode())
    return f"{key[:20]}:{hash_obj.hexdigest()}"


def cached(
    cache: Cache,
    prefix: str = "",
    ttl: Optional[int] = 3600,
    key_builder: Optional[Callable] = None,
) -> Callable:
    """
    Decorator để cache function results.

    Args:
        cache: Cache instance
        prefix: Key prefix
        ttl: Cache TTL (seconds)
        key_builder: Custom function để tạo cache key

    Returns:
        Decorated function

    Examples:
        >>> cache = InMemoryCache()
        >>> @cached(cache, prefix="test", ttl=60)
        ... def expensive_operation(x, y):
        ...     print("Computing...")
        ...     return x + y
        >>>
        >>> expensive_operation(1, 2)  # Will print "Computing..."
        Computing...
        3
        >>> expensive_operation(1, 2)  # No print, uses cached value
        3
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                func_prefix = f"{prefix}:{func.__module__}:{func.__name__}"
                cache_key = generate_cache_key(func_prefix, *args, **kwargs)

            cache_key = hash_cache_key(cache_key)

            # Check cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value

            # If not in cache, call function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                func_prefix = f"{prefix}:{func.__module__}:{func.__name__}"
                cache_key = generate_cache_key(func_prefix, *args, **kwargs)

            cache_key = hash_cache_key(cache_key)

            # Check cache first
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value

            # If not in cache, call function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result

        # Check if the function is async or not
        if hasattr(func, "__await__"):
            return async_wrapper
        return sync_wrapper

    return decorator


# Cache factory và initialization


def get_cache(cache_type: str = "memory") -> Cache:
    """
    Factory function để get cache instance.

    Args:
        cache_type: Type của cache ('memory' hoặc 'redis')

    Returns:
        Cache instance

    Examples:
        >>> memory_cache = get_cache("memory")
        >>> isinstance(memory_cache, InMemoryCache)
        True
    """
    if cache_type.lower() == "redis":
        try:
            from redis import Redis

            redis_host = "localhost"  # Can be loaded from config
            redis_port = 6379
            redis_client = Redis(host=redis_host, port=redis_port)
            return RedisCache(redis_client)
        except ImportError:
            logger.warning(
                "Redis package not installed, falling back to in-memory cache"
            )
            return InMemoryCache()
    else:
        return InMemoryCache()


# Global cache instance
default_cache = get_cache()


def clear_cache_by_prefix(prefix: str) -> None:
    """
    Clear cache entries by prefix.

    Args:
        prefix: Prefix để match cache keys

    Examples:
        >>> cache = InMemoryCache()
        >>> cache.set("test:1", "value1")
        >>> cache.set("test:2", "value2")
        >>> cache.set("other:1", "value3")
        >>> clear_cache_by_prefix("test")
        >>> cache.get("test:1") is None
        True
        >>> cache.get("other:1") is None
        False
    """
    if isinstance(default_cache, RedisCache):
        cursor = "0"
        pattern = f"{default_cache.prefix}{prefix}*"

        while cursor != 0:
            cursor, keys = default_cache.redis.scan(
                cursor=cursor, match=pattern
            )
            if keys:
                default_cache.redis.delete(*keys)
    elif isinstance(default_cache, InMemoryCache):
        keys_to_delete = [
            key for key in default_cache.cache.keys() if key.startswith(prefix)
        ]
        for key in keys_to_delete:
            default_cache.delete(key)
