import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

logger = logging.getLogger(__name__)


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


class InMemoryCacheService(CacheService):
    """In-memory implementation of cache service."""

    def __init__(self):
        """Initialize in-memory cache service."""
        self.cache: Dict[str, Dict[str, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        expires_at = entry.get("expires_at")

        # Check if expired
        if expires_at and expires_at < time.time():
            # Remove expired key
            await self.delete(key)
            return None

        return entry.get("value")

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        expires_at = None
        if ttl > 0:
            expires_at = time.time() + ttl

        self.cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": time.time(),
        }

        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self.cache:
            del self.cache[key]
        return True

    async def clear(self) -> bool:
        """Clear all cache."""
        self.cache.clear()
        return True


class JSONFileCacheService(CacheService):
    """JSON file-based implementation of cache service."""

    def __init__(self, cache_dir: str = "cache"):
        """Initialize JSON file cache service.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.meta_file = self.cache_dir / "meta.json"
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._load_metadata()

    def _load_metadata(self):
        """Load cache metadata from file."""
        try:
            if self.meta_file.exists():
                with open(self.meta_file, "r") as f:
                    self.metadata = json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache metadata: {e}")
            self.metadata = {}

    def _save_metadata(self):
        """Save cache metadata to file."""
        try:
            with open(self.meta_file, "w") as f:
                json.dump(self.metadata, f)
        except Exception as e:
            logger.error(f"Error saving cache metadata: {e}")

    def _get_cache_path(self, key: str) -> Path:
        """Get path to cache file for key."""
        # Use a hash of the key as the filename to avoid invalid characters
        filename = f"{hash(key)}.json"
        return self.cache_dir / filename

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache file."""
        try:
            # Check if key exists and is not expired
            if key not in self.metadata:
                return None

            entry = self.metadata[key]
            expires_at = entry.get("expires_at")

            # Check if expired
            if expires_at and expires_at < time.time():
                # Remove expired key
                await self.delete(key)
                return None

            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                # Metadata exists but file doesn't, clean up metadata
                del self.metadata[key]
                self._save_metadata()
                return None

            # Read the cache file
            with open(cache_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSON cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache file with TTL."""
        try:
            cache_path = self._get_cache_path(key)

            # Write the value to file
            with open(cache_path, "w") as f:
                json.dump(value, f)

            # Update metadata
            expires_at = None
            if ttl > 0:
                expires_at = time.time() + ttl

            self.metadata[key] = {
                "path": str(cache_path),
                "expires_at": expires_at,
                "created_at": time.time(),
            }

            self._save_metadata()
            return True
        except Exception as e:
            logger.error(f"JSON cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if key not in self.metadata:
                return True

            cache_path = self._get_cache_path(key)

            # Delete file if it exists
            if cache_path.exists():
                os.remove(cache_path)

            # Remove from metadata
            del self.metadata[key]
            self._save_metadata()
            return True
        except Exception as e:
            logger.error(f"JSON cache delete error: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cache."""
        try:
            # Delete all cache files
            for filename in os.listdir(self.cache_dir):
                file_path = self.cache_dir / filename
                if file_path.is_file() and filename != "meta.json":
                    os.remove(file_path)

            # Clear metadata
            self.metadata = {}
            self._save_metadata()
            return True
        except Exception as e:
            logger.error(f"JSON cache clear error: {e}")
            return False
