"""Helper functions for the Digital Metrics API."""

import hashlib
import json
from typing import Any, Dict


def generate_cache_key(prefix: str, params: Dict[str, Any]) -> str:
    """
    Generate a cache key from a prefix and parameters.

    Args:
        prefix: The prefix for the cache key
        params: Dictionary of parameters to be encoded in the key

    Returns:
        str: A unique cache key
    """
    # Sort params to ensure consistent keys
    sorted_params = {k: params[k] for k in sorted(params.keys())}

    # Serialize to JSON and hash
    params_str = json.dumps(sorted_params, sort_keys=True, default=str)
    hash_obj = hashlib.md5(params_str.encode())
    hash_str = hash_obj.hexdigest()

    return f"{prefix}:{hash_str}"


def truncate_string(text: str, max_length: int = 100) -> str:
    """
    Truncate a string to the specified maximum length.

    Args:
        text: The string to truncate
        max_length: Maximum length

    Returns:
        str: Truncated string with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
