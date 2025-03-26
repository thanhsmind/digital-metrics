"""Validation utilities cho Digital Metrics API."""

import re
from datetime import date, datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from fastapi import HTTPException, Query
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.models.core import DateRange, MetricsFilter
from app.utils.errors import ValidationError


def validate_model(
    data: Dict[str, Any], model_class: Type[BaseModel]
) -> BaseModel:
    """
    Validate dictionary data theo Pydantic model.

    Args:
        data: Dictionary data cần validate
        model_class: Pydantic model class để validate

    Returns:
        Instance của validated model

    Raises:
        HTTPException: Khi validation thất bại

    Examples:
        >>> from app.models import DateRange
        >>> data = {"start_date": "2023-01-01", "end_date": "2023-01-31"}
        >>> model = validate_model(data, DateRange)
        >>> isinstance(model, DateRange)
        True
    """
    try:
        return model_class(**data)
    except PydanticValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())


def validate_parameters(model_class: Type[BaseModel]):
    """
    Decorator để validate function parameters theo Pydantic model.

    Args:
        model_class: Pydantic model class để validate parameters

    Returns:
        Decorator function

    Examples:
        >>> from app.models import DateRange
        >>> @validate_parameters(DateRange)
        ... def process_dates(start_date, end_date):
        ...     return f"Processing dates from {start_date} to {end_date}"
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validated_params = model_class(**kwargs)
                # Replace original kwargs with validated ones
                kwargs.update(validated_params.dict())
                return func(*args, **kwargs)
            except PydanticValidationError as e:
                raise HTTPException(status_code=422, detail=e.errors())

        return wrapper

    return decorator


def sanitize_string(value: str) -> str:
    """
    Sanitize string input để ngăn XSS và SQL injection.

    Args:
        value: String cần sanitize

    Returns:
        Sanitized string

    Examples:
        >>> sanitize_string("<script>alert('XSS')</script>")
        'alert('XSS')'
        >>> sanitize_string("users--; DROP TABLE users;")
        'users DROP TABLE users'
    """
    # Remove potential script tags and SQL injection
    value = re.sub(r"<script.*?>.*?</script>", "", value, flags=re.DOTALL)
    value = re.sub(r"--", "", value)
    value = re.sub(r";", "", value)
    return value


def validate_list_items(
    items: List[Any],
    validator: Callable[[Any], bool],
    error_message: str = "Invalid item in list",
) -> List[Any]:
    """
    Validate mỗi item trong list theo validator function.

    Args:
        items: List các items cần validate
        validator: Function để validate mỗi item
        error_message: Message khi validation thất bại

    Returns:
        List các items đã pass validation

    Raises:
        ValueError: Khi có invalid items

    Examples:
        >>> numbers = [1, 2, 3, "4", 5]
        >>> validate_list_items(numbers, lambda x: isinstance(x, int))
        Traceback (most recent call last):
            ...
        ValueError: Invalid item in list: ['4']
    """
    invalid_items = [item for item in items if not validator(item)]
    if invalid_items:
        raise ValueError(f"{error_message}: {invalid_items}")
    return items


def validate_date_range(date_range: DateRange) -> None:
    """
    Validate DateRange object.

    Args:
        date_range: DateRange object cần validate

    Raises:
        ValidationError: Nếu date range không hợp lệ

    Examples:
        >>> from datetime import datetime
        >>> from app.models.core import DateRange
        >>> # Valid date range
        >>> valid_range = DateRange(
        ...     start_date=datetime(2023, 1, 1),
        ...     end_date=datetime(2023, 1, 31)
        ... )
        >>> validate_date_range(valid_range)  # No error
        >>>
        >>> # Invalid date range (start > end)
        >>> invalid_range = DateRange(
        ...     start_date=datetime(2023, 2, 1),
        ...     end_date=datetime(2023, 1, 1)
        ... )
        >>> validate_date_range(invalid_range)  # Raises ValidationError
    """
    # Ensure start_date is not in the future
    if date_range.start_date > datetime.now():
        raise ValidationError(
            "Start date cannot be in the future",
            details={"start_date": str(date_range.start_date)},
        )

    # Ensure start_date is before end_date
    if date_range.start_date > date_range.end_date:
        raise ValidationError(
            "Start date must be before end date",
            details={
                "start_date": str(date_range.start_date),
                "end_date": str(date_range.end_date),
            },
        )

    # Check for too long date ranges (e.g., more than 1 year)
    max_range = timedelta(days=366)
    if date_range.end_date - date_range.start_date > max_range:
        raise ValidationError(
            "Date range too large (maximum: 1 year)",
            details={
                "max_days": max_range.days,
                "requested_days": (
                    date_range.end_date - date_range.start_date
                ).days,
            },
        )


def validate_metrics(metrics: List[str], allowed_metrics: List[str]) -> None:
    """
    Validate list of metrics against allowed metrics.

    Args:
        metrics: List của metrics cần validate
        allowed_metrics: List của allowed metrics

    Raises:
        ValidationError: Nếu có invalid metrics

    Examples:
        >>> allowed = ["impressions", "clicks", "ctr", "spend"]
        >>> validate_metrics(["impressions", "clicks"], allowed)  # No error
        >>> validate_metrics(["invalid_metric"], allowed)  # Raises ValidationError
    """
    invalid_metrics = [m for m in metrics if m not in allowed_metrics]

    if invalid_metrics:
        raise ValidationError(
            "Invalid metrics specified",
            details={
                "invalid_metrics": invalid_metrics,
                "allowed_metrics": allowed_metrics,
            },
        )


def validate_dimensions(
    dimensions: List[str], allowed_dimensions: List[str]
) -> None:
    """
    Validate list of dimensions against allowed dimensions.

    Args:
        dimensions: List của dimensions cần validate
        allowed_dimensions: List của allowed dimensions

    Raises:
        ValidationError: Nếu có invalid dimensions

    Examples:
        >>> allowed = ["date", "campaign", "ad_group"]
        >>> validate_dimensions(["date", "campaign"], allowed)  # No error
        >>> validate_dimensions(["invalid_dim"], allowed)  # Raises ValidationError
    """
    if not dimensions:
        return

    invalid_dimensions = [d for d in dimensions if d not in allowed_dimensions]

    if invalid_dimensions:
        raise ValidationError(
            "Invalid dimensions specified",
            details={
                "invalid_dimensions": invalid_dimensions,
                "allowed_dimensions": allowed_dimensions,
            },
        )


def validate_metrics_filter(
    metrics_filter: MetricsFilter,
    allowed_metrics: List[str],
    allowed_dimensions: Optional[List[str]] = None,
) -> None:
    """
    Validate entire MetricsFilter object.

    Args:
        metrics_filter: MetricsFilter object cần validate
        allowed_metrics: List của allowed metrics
        allowed_dimensions: List của allowed dimensions (optional)

    Raises:
        ValidationError: Nếu filter không hợp lệ

    Examples:
        >>> from app.models.core import DateRange, MetricsFilter
        >>> from datetime import datetime
        >>> date_range = DateRange(
        ...     start_date=datetime(2023, 1, 1),
        ...     end_date=datetime(2023, 1, 31)
        ... )
        >>> filter = MetricsFilter(
        ...     date_range=date_range,
        ...     metrics=["impressions", "clicks"]
        ... )
        >>> allowed_metrics = ["impressions", "clicks", "ctr"]
        >>> validate_metrics_filter(filter, allowed_metrics)  # No error
    """
    # Validate date range
    validate_date_range(metrics_filter.date_range)

    # Validate metrics
    validate_metrics(metrics_filter.metrics, allowed_metrics)

    # Validate dimensions (if provided)
    if allowed_dimensions and metrics_filter.dimensions:
        validate_dimensions(metrics_filter.dimensions, allowed_dimensions)


def validate_api_key(
    api_key: str, pattern: str = r"^[a-zA-Z0-9_-]{16,64}$"
) -> bool:
    """
    Validate API key format.

    Args:
        api_key: API key cần validate
        pattern: Regex pattern cho valid API key

    Returns:
        True nếu API key hợp lệ, False nếu không

    Examples:
        >>> validate_api_key("valid-api-key-12345")
        True
        >>> validate_api_key("short")
        False
    """
    if not api_key:
        return False

    return bool(re.match(pattern, api_key))


def validate_pagination_params(
    page: int, page_size: int, max_page_size: int = 100
) -> Tuple[int, int]:
    """
    Validate và normalize pagination parameters.

    Args:
        page: Page number (1-based)
        page_size: Items per page
        max_page_size: Maximum allowed page size

    Returns:
        Tuple (normalized_page, normalized_page_size)

    Raises:
        ValidationError: Nếu parameters không hợp lệ

    Examples:
        >>> validate_pagination_params(1, 20)
        (1, 20)
        >>> validate_pagination_params(0, 200, max_page_size=100)
        (1, 100)
    """
    # Normalize page
    normalized_page = max(1, page)

    # Normalize page_size
    normalized_page_size = min(max(1, page_size), max_page_size)

    if page < 1:
        raise ValidationError(
            "Page number must be at least 1",
            details={"provided": page, "normalized": normalized_page},
        )

    if page_size < 1:
        raise ValidationError(
            "Page size must be at least 1",
            details={"provided": page_size, "normalized": normalized_page_size},
        )

    if page_size > max_page_size:
        raise ValidationError(
            f"Page size exceeds maximum allowed value ({max_page_size})",
            details={
                "provided": page_size,
                "max_allowed": max_page_size,
                "normalized": normalized_page_size,
            },
        )

    return normalized_page, normalized_page_size


def validate_sort_params(
    sort_by: str,
    sort_order: str,
    allowed_fields: List[str],
    allowed_orders: List[str] = ["asc", "desc"],
) -> Tuple[str, str]:
    """
    Validate sorting parameters.

    Args:
        sort_by: Field name để sort
        sort_order: Order của sort (asc/desc)
        allowed_fields: List các field được phép sort
        allowed_orders: List các order được phép

    Returns:
        Tuple (validated_sort_by, validated_sort_order)

    Raises:
        ValidationError: Nếu sort parameters không hợp lệ

    Examples:
        >>> validate_sort_params("date", "asc", ["date", "impressions"])
        ('date', 'asc')
        >>> validate_sort_params("invalid", "asc", ["date"])  # Raises ValidationError
    """
    sort_order = sort_order.lower()

    if sort_by not in allowed_fields:
        raise ValidationError(
            "Invalid sort field",
            details={"provided": sort_by, "allowed": allowed_fields},
        )

    if sort_order not in allowed_orders:
        raise ValidationError(
            "Invalid sort order",
            details={"provided": sort_order, "allowed": allowed_orders},
        )

    return sort_by, sort_order
