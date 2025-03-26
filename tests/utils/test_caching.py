"""Tests cho caching utilities."""

import time
import unittest
from datetime import datetime, timedelta
from functools import wraps

from app.utils.caching import (
    Cache,
    InMemoryCache,
    cached,
    generate_cache_key,
    hash_cache_key,
)


class TestCachingUtils(unittest.TestCase):
    """Test cases cho caching utils."""

    def setUp(self):
        """Set up test environment."""
        self.cache = InMemoryCache()

    def test_in_memory_cache_basic(self):
        """Test basic InMemoryCache operations."""
        # Test set & get
        self.cache.set("test_key", "test_value")
        self.assertEqual(self.cache.get("test_key"), "test_value")

        # Test non-existent key
        self.assertIsNone(self.cache.get("non_existent"))

        # Test delete
        self.cache.delete("test_key")
        self.assertIsNone(self.cache.get("test_key"))

        # Test clear
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_in_memory_cache_ttl(self):
        """Test TTL functionality of InMemoryCache."""
        # Set a key with TTL of 0.1 seconds
        self.cache.set("key_with_ttl", "value", ttl=0.1)

        # Should be able to get immediately
        self.assertEqual(self.cache.get("key_with_ttl"), "value")

        # Wait for TTL to expire
        time.sleep(0.2)

        # Key should have expired
        self.assertIsNone(self.cache.get("key_with_ttl"))

    def test_generate_cache_key(self):
        """Test generate_cache_key function."""
        # Test with prefix only
        self.assertEqual(generate_cache_key("test"), "test")

        # Test with args
        self.assertEqual(
            generate_cache_key("metrics", "facebook", "clicks"),
            "metrics:facebook:clicks",
        )

        # Test with kwargs
        self.assertEqual(
            generate_cache_key("metrics", platform="facebook", metric="clicks"),
            "metrics:metric=clicks:platform=facebook",
        )

        # Test with both args and kwargs
        self.assertEqual(
            generate_cache_key("metrics", "campaign", start_date="2023-01-01"),
            "metrics:campaign:start_date=2023-01-01",
        )

    def test_hash_cache_key(self):
        """Test hash_cache_key function."""
        # Short key should remain unchanged
        short_key = "test_key"
        self.assertEqual(hash_cache_key(short_key), short_key)

        # Long key should be hashed
        long_key = "a" * 200
        hashed = hash_cache_key(long_key)

        # Hashed key should be shorter
        self.assertLess(len(hashed), 100)

        # Hashed key should start with original prefix
        self.assertTrue(hashed.startswith(long_key[:20]))

    def test_cached_decorator_sync(self):
        """Test cached decorator with synchronous functions."""
        call_count = 0

        @cached(self.cache, prefix="test", ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # First call should execute function
        result1 = expensive_function(5, 10)
        self.assertEqual(result1, 15)
        self.assertEqual(call_count, 1)

        # Second call with same args should use cache
        result2 = expensive_function(5, 10)
        self.assertEqual(result2, 15)
        self.assertEqual(call_count, 1)  # Should not increase

        # Call with different args should execute function again
        result3 = expensive_function(10, 20)
        self.assertEqual(result3, 30)
        self.assertEqual(call_count, 2)

    def test_cached_decorator_custom_key_builder(self):
        """Test cached decorator with custom key builder."""
        call_count = 0

        def custom_key_builder(x, y):
            return f"custom:sum:{x+y}"

        @cached(self.cache, key_builder=custom_key_builder)
        def my_function(x, y):
            nonlocal call_count
            call_count += 1
            return x * y

        # These calls should have the same cache key despite different args
        result1 = my_function(2, 3)  # sum = 5
        self.assertEqual(result1, 6)
        self.assertEqual(call_count, 1)

        result2 = my_function(1, 4)  # sum = 5
        self.assertEqual(result2, 6)  # Should return first result
        self.assertEqual(call_count, 1)  # Should not increase


if __name__ == "__main__":
    unittest.main()
