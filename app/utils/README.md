# Digital Metrics API - Utilities

Package này chứa các utility functions và tools dùng trong Digital Metrics API.

## Cấu trúc

- `__init__.py`: Exports tất cả utilities
- `caching.py`: Caching utilities (in-memory)
- `config.py`: Configuration loading và management
- `errors.py`: Error handling và custom exceptions
- `formatting.py`: Data formatting utilities
- `logging.py`: Logging utilities và configuration
- `testing.py`: Testing utilities và fake data generators
- `validation.py`: Data validation utilities

## Các Utility Functions

### Caching Utilities

Hỗ trợ caching với in-memory:

```python
from app.utils import cached, default_cache

# Cache function result cho 60 giây
@cached(default_cache, ttl=60)
def expensive_operation(arg1, arg2):
    # Long-running operation
    return result
```

### Error Handling

Custom exceptions và error serialization:

```python
from app.utils import ValidationError, add_exception_handlers

# Đăng ký error handlers
add_exception_handlers(app)

# Sử dụng custom errors
if not valid_data:
    raise ValidationError("Invalid input data", details={"field": "email"})
```

### Logging

Custom logging với support cho JSON format:

```python
from app.utils import get_logger

logger = get_logger("my_module")
logger.info("Processing data", count=5, status="success")
```

### Formatting

Format data cho output:

```python
from app.utils import format_currency, format_metrics_data

# Format số thành currency
money = format_currency(1234.56)  # "$1,234.56"

# Format metrics data
formatted = format_metrics_data(data, {
    "impressions": "large_number",
    "ctr": "percent"
})
```

### Validation

Validate input data:

```python
from app.utils import validate_date_range, validate_metrics_filter

# Validate date range
validate_date_range(date_range)

# Validate metrics filter
validate_metrics_filter(filter, allowed_metrics=["impressions", "clicks"])
```

### Configuration

Load và manage configuration:

```python
from app.utils import get_config

# Load config từ environment variables hoặc file
config = get_config()
database_url = config.database.get_connection_string()
```

### Testing

Generate test data và mocks:

```python
from app.utils import generate_metrics_data, mock_facebook_campaign_response

# Generate fake metrics data
test_data = generate_metrics_data(date_range, ["impressions", "clicks"])

# Generate mock API response
mock_response = mock_facebook_campaign_response()
```

## Các Best Practices

1. **Error Handling**: Luôn sử dụng custom exceptions để error messages nhất quán
2. **Validation**: Validate input data sớm trong request lifecycle
3. **Logging**: Use structured logging với context (user_id, request_id, etc.)
4. **Caching**: Cache expensive operations nhưng set TTL phù hợp
5. **Testing**: Use test utilities để generate test data thay vì hardcoded data
