import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from prometheus_client import CollectorRegistry
from redis import Redis

from services.cache_service import RedisCacheService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def registry():
    """Create a new registry for each test."""
    return CollectorRegistry()


@pytest.fixture
def mock_redis():
    redis = MagicMock(spec=Redis)
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.flushdb = AsyncMock()
    return redis


@pytest.fixture
def cache_service(mock_redis, registry):
    service = RedisCacheService(mock_redis)
    service.metrics = service.metrics.__class__(registry=registry)
    return service


async def test_get_cache_hit(cache_service, mock_redis):
    """Test successful cache get with existing key."""
    test_data = {"key": "value"}
    mock_redis.get.return_value = json.dumps(test_data)

    result = await cache_service.get("test_key")

    assert result == test_data
    mock_redis.get.assert_called_once_with("test_key")


async def test_get_cache_miss(cache_service, mock_redis):
    """Test cache get with non-existing key."""
    mock_redis.get.return_value = None

    result = await cache_service.get("test_key")

    assert result is None
    mock_redis.get.assert_called_once_with("test_key")


async def test_set_cache(cache_service, mock_redis):
    """Test successful cache set."""
    test_data = {"key": "value"}
    mock_redis.set.return_value = True

    result = await cache_service.set("test_key", test_data, 300)

    assert result is True
    mock_redis.set.assert_called_once_with(
        "test_key", json.dumps(test_data), ex=300
    )


async def test_delete_cache(cache_service, mock_redis):
    """Test successful cache delete."""
    mock_redis.delete.return_value = 1

    result = await cache_service.delete("test_key")

    assert result is True
    mock_redis.delete.assert_called_once_with("test_key")


async def test_clear_cache(cache_service, mock_redis):
    """Test successful cache clear."""
    mock_redis.flushdb.return_value = True

    result = await cache_service.clear()

    assert result is True
    mock_redis.flushdb.assert_called_once()


async def test_cache_error_handling(cache_service, mock_redis):
    """Test error handling in cache operations."""
    mock_redis.get.side_effect = Exception("Redis error")

    result = await cache_service.get("test_key")

    assert result is None
    mock_redis.get.assert_called_once_with("test_key")
