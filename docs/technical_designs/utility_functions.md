# Technical Design Document: Utility Functions Implementation

## 1. Tổng Quan

Document này mô tả chi tiết thiết kế và triển khai các utility functions cho Digital Metrics API. Các utility functions cung cấp các chức năng thường xuyên sử dụng trong toàn bộ codebase, giúp giảm code duplication, tăng tính nhất quán và dễ bảo trì.

## 2. Yêu Cầu

### 2.1 Yêu Cầu Chức Năng

#### Date Handling Utilities

- Là một developer, tôi muốn standardize date formats trong toàn bộ ứng dụng
- Là một developer, tôi muốn validate date ranges dễ dàng
- Là một developer, tôi muốn so sánh dates và tính toán độ chênh lệch

#### Validation Utilities

- Là một developer, tôi muốn validate user inputs để tránh bad data
- Là một developer, tôi muốn có decorators để validate parameters tự động
- Là một developer, tôi muốn sanitize inputs để ngăn security issues

#### Error Handling Utilities

- Là một developer, tôi muốn define custom exceptions cho các trường hợp lỗi cụ thể
- Là một developer, tôi muốn serialize exceptions thành JSON responses
- Là một developer, tôi muốn handling errors gracefully trong API endpoints

#### Testing Utilities

- Là một developer, tôi muốn generate test data nhanh chóng
- Là một developer, tôi muốn mock external services responses
- Là một developer, tôi muốn có helpers cho unit và integration tests

### 2.2 Yêu Cầu Phi Chức Năng

- Code phải được tái sử dụng trong toàn bộ codebase
- Đầy đủ unit tests cho mỗi function
- Documentation cho tất cả các functions
- Tương thích với FastAPI và Pydantic
- Thread-safe và performance optimized

## 3. Thiết Kế Kỹ Thuật

### 3.1 Date Handling Utilities

```python
# app/utils/date.py

from datetime import datetime, timedelta
from typing import Optional, Tuple, Union

from app.models.core import DateRange

DEFAULT_DATE_FORMAT = "%Y-%m-%d"

def format_date(date: Union[datetime, str], output_format: str = DEFAULT_DATE_FORMAT) -> str:
    """Chuẩn hóa date thành string theo định dạng cụ thể."""
    if isinstance(date, str):
        date = parse_date(date)
    return date.strftime(output_format)

def parse_date(date_str: str, input_format: Optional[str] = None) -> datetime:
    """Parse date string thành datetime object."""
    if input_format:
        return datetime.strptime(date_str, input_format)

    # Try common formats
    formats = [DEFAULT_DATE_FORMAT, "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Cannot parse date string: {date_str}")

def validate_date_range(start_date: Union[datetime, str], end_date: Union[datetime, str]) -> Tuple[datetime, datetime]:
    """Validate date range và trả về tuple of datetime objects."""
    if isinstance(start_date, str):
        start_date = parse_date(start_date)

    if isinstance(end_date, str):
        end_date = parse_date(end_date)

    if end_date < start_date:
        raise ValueError("End date must be after start date")

    return start_date, end_date

def get_date_diff_days(start_date: Union[datetime, str], end_date: Union[datetime, str]) -> int:
    """Tính số ngày giữa hai dates."""
    start, end = validate_date_range(start_date, end_date)
    return (end - start).days

def get_previous_period(date_range: DateRange) -> DateRange:
    """Tính previous period với cùng độ dài."""
    delta = (date_range.end_date - date_range.start_date)

    prev_end = date_range.start_date - timedelta(days=1)
    prev_start = prev_end - delta

    return DateRange(start_date=prev_start, end_date=prev_end)
```

### 3.2 Validation Utilities

```python
# app/utils/validation.py

import re
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union

from fastapi import HTTPException, Query
from pydantic import BaseModel, ValidationError

def validate_model(data: Dict[str, Any], model_class: Type[BaseModel]) -> BaseModel:
    """Validate dictionary data theo Pydantic model."""
    try:
        return model_class(**data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

def validate_parameters(model_class: Type[BaseModel]):
    """Decorator để validate function parameters theo Pydantic model."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validated_params = model_class(**kwargs)
                # Replace original kwargs with validated ones
                kwargs.update(validated_params.dict())
                return func(*args, **kwargs)
            except ValidationError as e:
                raise HTTPException(status_code=422, detail=e.errors())
        return wrapper
    return decorator

def sanitize_string(value: str) -> str:
    """Sanitize string input để ngăn XSS và SQL injection."""
    # Remove potential script tags and SQL injection
    value = re.sub(r'<script.*?>.*?</script>', '', value, flags=re.DOTALL)
    value = re.sub(r'--', '', value)
    value = re.sub(r';', '', value)
    return value

def validate_list_items(items: List[Any], validator: Callable[[Any], bool],
                        error_message: str = "Invalid item in list") -> List[Any]:
    """Validate mỗi item trong list theo validator function."""
    invalid_items = [item for item in items if not validator(item)]
    if invalid_items:
        raise ValueError(f"{error_message}: {invalid_items}")
    return items
```

### 3.3 Error Handling Utilities

```python
# app/utils/errors.py

from typing import Any, Dict, List, Optional, Type, Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Custom exception classes
class APIError(Exception):
    """Base class cho tất cả API errors."""
    def __init__(self,
                 message: str,
                 status_code: int = 500,
                 error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

class ValidationError(APIError):
    """Error khi validation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )

class AuthenticationError(APIError):
    """Error khi authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )

class NotFoundError(APIError):
    """Error khi resource không tồn tại."""
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID {resource_id} not found"

        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND_ERROR"
        )

# Error serialization
def serialize_error(error: Union[APIError, Exception]) -> Dict[str, Any]:
    """Serialize error thành JSON response."""
    if isinstance(error, APIError):
        error_response = {
            "success": False,
            "message": error.message,
            "error_code": error.error_code
        }
        if error.details:
            error_response["details"] = error.details
        return error_response

    # Generic error
    return {
        "success": False,
        "message": str(error),
        "error_code": "INTERNAL_SERVER_ERROR"
    }

# Exception handlers
def add_exception_handlers(app: FastAPI) -> None:
    """Add tất cả exception handlers to FastAPI app."""
    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, error: APIError):
        return JSONResponse(
            status_code=error.status_code,
            content=serialize_error(error)
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, error: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Invalid request parameters",
                "error_code": "VALIDATION_ERROR",
                "details": error.errors()
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, error: StarletteHTTPException):
        return JSONResponse(
            status_code=error.status_code,
            content={
                "success": False,
                "message": error.detail,
                "error_code": f"HTTP_ERROR_{error.status_code}"
            }
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, error: Exception):
        return JSONResponse(
            status_code=500,
            content=serialize_error(error)
        )
```

### 3.4 Testing Utilities

```python
# app/utils/testing.py

import json
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from app.models.core import DateRange, MetricsFilter

# Test data generators
def generate_date_range(days_ago: int = 30, days_range: int = 30) -> DateRange:
    """Generate DateRange từ X days ago cho Y days."""
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days_ago)
    end_date = start_date + timedelta(days=days_range)

    return DateRange(start_date=start_date, end_date=end_date)

def generate_metrics_filter(metrics: Optional[List[str]] = None,
                           dimensions: Optional[List[str]] = None) -> MetricsFilter:
    """Generate MetricsFilter với metrics và dimensions cụ thể."""
    if metrics is None:
        metrics = ["impressions", "clicks", "ctr", "spend"]

    return MetricsFilter(
        date_range=generate_date_range(),
        metrics=metrics,
        dimensions=dimensions
    )

def generate_metrics_data(date_range: DateRange,
                         metrics: List[str],
                         dimensions: Optional[List[str]] = None,
                         num_rows: int = 10) -> List[Dict[str, Any]]:
    """Generate fake metrics data."""
    data = []
    current_date = date_range.start_date
    delta = (date_range.end_date - date_range.start_date).days

    for _ in range(num_rows):
        row = {}

        # Add date dimension
        random_day = random.randint(0, delta)
        row_date = current_date + timedelta(days=random_day)
        row["date"] = row_date.strftime("%Y-%m-%d")

        # Add custom dimensions
        if dimensions:
            for dim in dimensions:
                row[dim] = f"{dim}_{random.randint(1, 5)}"

        # Add metrics
        for metric in metrics:
            if metric in ["ctr", "cvr"]:
                row[metric] = round(random.uniform(0.01, 0.1), 4)
            else:
                row[metric] = random.randint(100, 10000)

        data.append(row)

    return data

# Mock response generators
def mock_facebook_campaign_response() -> Dict[str, Any]:
    """Generate mock Facebook campaigns API response."""
    return {
        "data": [
            {"id": f"campaign_{i}", "name": f"Campaign {i}"}
            for i in range(1, 6)
        ],
        "paging": {
            "cursors": {
                "before": "MAZDZD",
                "after": "MTNDY2"
            },
            "next": "https://graph.facebook.com/v13.0/next_page"
        }
    }

def mock_facebook_metrics_response(metrics: List[str]) -> Dict[str, Any]:
    """Generate mock Facebook metrics API response."""
    date_range = generate_date_range()
    return {
        "data": generate_metrics_data(date_range, metrics),
        "summary": {
            metric: random.randint(1000, 100000)
            for metric in metrics if metric not in ["ctr", "cvr"]
        }
    }

def mock_google_campaign_response() -> Dict[str, Any]:
    """Generate mock Google campaigns API response."""
    return {
        "results": [
            {
                "campaign": {
                    "resourceName": f"customers/123/campaigns/{i}",
                    "id": f"{i}",
                    "name": f"Google Campaign {i}"
                }
            }
            for i in range(1, 6)
        ],
        "nextPageToken": "abc123"
    }

# Test helper functions
def load_test_data(file_path: str) -> Any:
    """Load test data from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)

def validate_response_structure(response: Dict[str, Any], required_fields: List[str]) -> bool:
    """Validate response chứa tất cả required fields."""
    return all(field in response for field in required_fields)
```

### 3.5 Patterns và Best Practices

1. **Immutable Objects**: Sử dụng immutable objects khi có thể để tránh side effects.
2. **Type Hinting**: Sử dụng Python type hinting cho tất cả functions để tăng tính rõ ràng.
3. **DRY (Don't Repeat Yourself)**: Refactor common code vào utility functions.
4. **SOLID Principles**: Theo các SOLID principles khi thiết kế classes và functions.
5. **Error Handling**: Handle exceptions gracefully với thông báo lỗi rõ ràng.
6. **Documentation**: Tất cả functions phải có docstrings và type hints.
7. **Testing**: Unit tests cho mỗi utility function với các test cases khác nhau.

## 4. Testing

### 4.1 Unit Tests cho Date Utilities

```python
# tests/utils/test_date.py

import pytest
from datetime import datetime, timedelta

from app.utils.date import (
    format_date, parse_date, validate_date_range,
    get_date_diff_days, get_previous_period
)
from app.models.core import DateRange

def test_format_date():
    """Test format_date function."""
    date = datetime(2023, 1, 15)
    assert format_date(date) == "2023-01-15"
    assert format_date(date, "%d/%m/%Y") == "15/01/2023"

    # Test with string input
    assert format_date("2023-01-15") == "2023-01-15"

def test_parse_date():
    """Test parse_date function."""
    # Test with format specified
    assert parse_date("15/01/2023", "%d/%m/%Y") == datetime(2023, 1, 15)

    # Test auto format detection
    assert parse_date("2023-01-15") == datetime(2023, 1, 15)
    assert parse_date("15/01/2023") == datetime(2023, 1, 15)
    assert parse_date("01/15/2023") == datetime(2023, 1, 15)

    # Test invalid format
    with pytest.raises(ValueError):
        parse_date("invalid-date")

def test_validate_date_range():
    """Test validate_date_range function."""
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)

    # Test with datetime objects
    assert validate_date_range(start_date, end_date) == (start_date, end_date)

    # Test with string inputs
    assert validate_date_range("2023-01-01", "2023-01-31") == (
        datetime(2023, 1, 1),
        datetime(2023, 1, 31)
    )

    # Test invalid range
    with pytest.raises(ValueError):
        validate_date_range(end_date, start_date)

def test_get_date_diff_days():
    """Test get_date_diff_days function."""
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 31)

    assert get_date_diff_days(start_date, end_date) == 30
    assert get_date_diff_days("2023-01-01", "2023-01-31") == 30

def test_get_previous_period():
    """Test get_previous_period function."""
    current_period = DateRange(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 31)
    )

    prev_period = get_previous_period(current_period)

    assert prev_period.end_date == datetime(2022, 12, 31)
    assert prev_period.start_date == datetime(2022, 12, 1)
    assert (prev_period.end_date - prev_period.start_date) == (
        current_period.end_date - current_period.start_date
    )
```

### 4.2 Unit Tests cho Validation Utilities

### 4.3 Unit Tests cho Error Handling Utilities

### 4.4 Unit Tests cho Testing Utilities

## 5. Khả Năng Mở Rộng

1. **Mở rộng Date Utilities:**

   - Thêm xử lý timezone
   - Thêm formatting theo locale
   - Hỗ trợ các period types khác (week, month, quarter, year)

2. **Mở rộng Validation Utilities:**

   - Thêm complex validation rules
   - Thêm điều kiện validation dựa trên context
   - Thêm schema-based validation

3. **Mở rộng Error Handling:**

   - Thêm error tracking (Sentry, etc.)
   - Thêm custom error types cho Facebook/Google APIs
   - Thêm internationalization cho error messages

4. **Mở rộng Testing Utilities:**
   - Thêm integration test helpers
   - Thêm performance test utilities
   - Thêm MockResponse classes cho external APIs

## 6. Câu Hỏi Mở

- Có nên group các utilities theo functional areas hay theo technical areas?
- Sử dụng third-party libraries hay custom implementations cho common utilities?
- Mức độ abstraction phù hợp cho utilities để balance giữa flexibility và usability?
- Làm thế nào để đảm bảo consistency trong error handling giữa các services?

## 7. Giải Pháp Thay Thế

1. **Third-party libraries:**

   - Arrow thay vì custom date utilities
   - marshmallow thay vì custom validation
   - python-toolbox cho utility functions

2. **Functional Programming Approach:**

   - Sử dụng functional programming pattern thay vì class-based utilities
   - Leverage functools cho higher-order functions
   - Sử dụng pure functions để tăng testability

3. **Context Managers:**
   - Sử dụng context managers cho error handling
   - Sử dụng context-based validation
