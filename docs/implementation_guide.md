# Digital Metrics Implementation Guide

## Project Structure

```
digital-metrics/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── facebook/
│   │   │   │   ├── routes.py
│   │   │   │   └── schemas.py
│   │   │   └── google/
│   │   │       ├── routes.py
│   │   │       └── schemas.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── errors.py
│   │   ├── models/
│   │   │   ├── facebook.py
│   │   │   └── google.py
│   │   ├── services/
│   │   │   ├── facebook.py
│   │   │   └── google.py
│   │   └── utils/
│   │       ├── cache.py
│   │       └── metrics.py
│   ├── tests/
│   │   ├── api/
│   │   ├── services/
│   │   └── utils/
│   └── docs/
│       ├── technical_design.md
│       ├── tasks.md
│       └── implementation_guide.md
```

## Coding Standards

### Python & FastAPI

1. **Type Hints:**

```python
from typing import List, Optional, Dict, Any
from datetime import datetime

async def get_campaign_metrics(
    campaign_id: str,
    start_date: datetime,
    end_date: datetime,
    metrics: List[str]
) -> Dict[str, Any]:
    """
    Lấy metrics của một campaign.

    Args:
        campaign_id: ID của campaign
        start_date: Ngày bắt đầu
        end_date: Ngày kết thúc
        metrics: Danh sách metrics cần lấy

    Returns:
        Dict chứa metrics data

    Raises:
        FacebookAPIError: Khi có lỗi từ Facebook API
    """
    pass
```

2. **Models:**

```python
from pydantic import BaseModel, Field

class MetricsRequest(BaseModel):
    campaign_id: str = Field(..., description="Campaign ID")
    metrics: List[str] = Field(..., description="List of metrics to fetch")
    start_date: datetime
    end_date: datetime

    class Config:
        schema_extra = {
            "example": {
                "campaign_id": "123456789",
                "metrics": ["impressions", "clicks"],
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-31T23:59:59Z"
            }
        }
```

3. **API Endpoints:**

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter()

@router.get("/campaigns/{campaign_id}/metrics")
async def get_campaign_metrics(
    campaign_id: str,
    metrics: List[str],
    service: FacebookService = Depends(get_facebook_service)
) -> MetricsResponse:
    try:
        return await service.get_metrics(campaign_id, metrics)
    except FacebookAPIError as e:
        raise HTTPException(status_code=503, detail=str(e))
```

4. **Services:**

```python
class FacebookService:
    def __init__(self, cache: RedisCache, client: FacebookAdsApi):
        self.cache = cache
        self.client = client

    async def get_metrics(
        self,
        campaign_id: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        cache_key = f"fb_metrics:{campaign_id}"

        # Check cache
        if cached := await self.cache.get(cache_key):
            return cached

        # Get from API
        try:
            data = await self.client.get_metrics(campaign_id, metrics)
            await self.cache.set(cache_key, data, ttl=300)
            return data
        except Exception as e:
            logger.error(f"Facebook API error: {e}")
            raise FacebookAPIError(str(e))
```

### Error Handling

1. **Custom Exceptions:**

```python
class FacebookAPIError(Exception):
    """Raised when there is an error with Facebook API."""
    pass

class GoogleAPIError(Exception):
    """Raised when there is an error with Google Ads API."""
    pass

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass
```

2. **Error Responses:**

```python
from fastapi import HTTPException
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

async def get_metrics(campaign_id: str) -> Dict[str, Any]:
    try:
        return await facebook_service.get_metrics(campaign_id)
    except FacebookAPIError as e:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "Facebook API error",
                "error": str(e)
            }
        )
```

### Caching

1. **Redis Cache:**

```python
from redis import Redis
from typing import Optional, Any
import json

class RedisCache:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[Any]:
        if data := await self.redis.get(key):
            return json.loads(data)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ) -> None:
        await self.redis.set(
            key,
            json.dumps(value),
            ex=ttl
        )
```

### Testing

1. **Unit Tests:**

```python
import pytest
from unittest.mock import Mock, patch

def test_facebook_metrics():
    # Arrange
    service = FacebookService(mock_cache, mock_client)

    # Act
    metrics = await service.get_metrics("123", ["impressions"])

    # Assert
    assert "impressions" in metrics
    mock_client.get_metrics.assert_called_once()
```

2. **Integration Tests:**

```python
@pytest.mark.integration
async def test_facebook_api_integration():
    # Setup
    client = TestClient(app)

    # Test
    response = client.get("/api/v1/facebook/campaigns/123/metrics")

    # Assert
    assert response.status_code == 200
    assert "data" in response.json()
```

## Deployment

1. **Environment Variables:**

```env
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
REDIS_URL=redis://localhost:6379
```

2. **Docker Configuration:**

```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Monitoring

1. **Logging:**

```python
import logging

logger = logging.getLogger(__name__)

async def get_metrics():
    try:
        logger.info("Fetching metrics from Facebook")
        return await facebook_service.get_metrics()
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise
```

2. **Metrics:**

```python
from prometheus_client import Counter, Histogram

requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)
```

## Security

1. **Authentication:**

```python
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401)
```

2. **Rate Limiting:**

```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/metrics")
@limiter.limit("100/minute")
async def get_metrics(request: Request):
    return await service.get_metrics()
```
