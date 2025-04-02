"""Caching utilities cho Digital Metrics API."""

import hashlib
import json
import pickle
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from fastapi import Depends, Request

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
    In-memory cache implementation, phù hợp cho development và testing.
    """

    def __init__(self):
        """Initialize cache storage."""
        self.cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value từ in-memory cache.

        Args:
            key: Cache key

        Returns:
            Cached value hoặc None nếu không có hoặc đã hết hạn
        """
        if key not in self.cache:
            return None

        cache_item = self.cache[key]
        expires_at = cache_item.get("expires_at")

        # Kiểm tra expiration
        if expires_at and expires_at < datetime.now():
            # Cache đã hết hạn
            self.delete(key)
            return None

        return cache_item.get("value")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value vào in-memory cache.

        Args:
            key: Cache key
            value: Value cần cache
            ttl: Time to live (seconds)
        """
        cache_item = {"value": value}

        if ttl is not None:
            cache_item["expires_at"] = datetime.now() + timedelta(seconds=ttl)

        self.cache[key] = cache_item

    def delete(self, key: str) -> None:
        """
        Xóa key từ in-memory cache.

        Args:
            key: Cache key
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear entire in-memory cache."""
        self.cache.clear()


# Cache factory và initialization


def get_cache() -> Cache:
    """
    Factory function để get cache instance.

    Returns:
        InMemoryCache instance
    """
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
    if isinstance(default_cache, InMemoryCache):
        keys_to_delete = [
            key for key in default_cache.cache.keys() if key.startswith(prefix)
        ]
        for key in keys_to_delete:
            default_cache.delete(key)


# Cache decorators


def cached(
    ttl: int = 300,
    prefix: str = "",
    key_builder: Optional[Callable] = None,
):
    """
    Decorator để cache function results.

    Args:
        ttl: Time to live (seconds)
        prefix: Prefix cho cache key
        key_builder: Function để build cache key từ function args/kwargs

    Returns:
        Decorated function

    Examples:
        >>> @cached(ttl=10)
        ... def slow_function(a, b):
        ...     return a + b
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key từ function name và params
                params = []
                params.extend(
                    str(arg)
                    for arg in args
                    if isinstance(arg, (str, int, float, bool))
                )
                params.extend(
                    f"{k}:{v}"
                    for k, v in kwargs.items()
                    if isinstance(v, (str, int, float, bool))
                )
                serialized_params = ":".join(params)

                # Hash serialized_params nếu quá dài
                if len(serialized_params) > 100:
                    serialized_params = hashlib.md5(
                        serialized_params.encode()
                    ).hexdigest()

                cache_key = f"{prefix}{func.__name__}:{serialized_params}"

            # Try to get from cache
            cached_result = default_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            logger.debug(f"Cache miss for {cache_key}")
            # Execute function và cache result
            result = await func(*args, **kwargs)
            default_cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
