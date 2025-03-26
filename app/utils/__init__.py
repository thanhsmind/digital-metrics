"""Utils package cho Digital Metrics API."""

from app.utils.caching import (
    Cache,
    InMemoryCache,
    RedisCache,
    cached,
    default_cache,
    get_cache,
)
from app.utils.config import get_config, load_app_config
from app.utils.errors import (
    APIError,
    AuthenticationError,
    ConfigError,
    NotFoundError,
    ValidationError,
    add_exception_handlers,
    serialize_error,
)
from app.utils.formatting import (
    format_currency,
    format_date,
    format_large_number,
    format_metrics_data,
    format_percent,
    to_camel_case,
    to_snake_case,
)
from app.utils.logging import APILogger, get_logger, setup_app_logging
from app.utils.testing import (
    generate_date_range,
    generate_metrics_data,
    generate_metrics_filter,
    mock_facebook_campaign_response,
    mock_facebook_metrics_response,
    mock_google_campaign_response,
)
from app.utils.validation import (
    validate_api_key,
    validate_date_range,
    validate_dimensions,
    validate_metrics,
    validate_metrics_filter,
    validate_pagination_params,
    validate_sort_params,
)

__all__ = [
    # Date utilities
    "format_date",
    "parse_date",
    "validate_date_range",
    "get_date_diff_days",
    "get_previous_period",
    # Validation utilities
    "validate_model",
    "validate_parameters",
    "sanitize_string",
    "validate_list_items",
    # Error utilities
    "APIError",
    "ValidationError",
    "AuthenticationError",
    "NotFoundError",
    "serialize_error",
    "add_exception_handlers",
]
