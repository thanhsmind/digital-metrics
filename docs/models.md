# Digital Metrics - Core Models

## Overview

Document này mô tả các core models được sử dụng trong Digital Metrics API. Các models này là nền tảng cho việc xây dựng API endpoints và xử lý dữ liệu.

## Core Models

### DateRange

`DateRange` là model đại diện cho một khoảng thời gian trong báo cáo metrics.

```python
class DateRange(BaseModel):
    start_date: datetime
    end_date: datetime
```

**Properties:**

- `start_date`: Ngày bắt đầu của khoảng thời gian (datetime)
- `end_date`: Ngày kết thúc của khoảng thời gian (datetime)

**Validation:**

- `end_date` phải sau `start_date`

**Ví dụ:**

```python
date_range = DateRange(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 1, 31)
)
```

### MetricsFilter

`MetricsFilter` là model dùng để lọc và phân tích metrics từ Facebook và Google Ads.

```python
class MetricsFilter(BaseModel):
    date_range: DateRange
    metrics: List[str]
    dimensions: Optional[List[str]] = None
```

**Properties:**

- `date_range`: Khoảng thời gian cho metrics (DateRange)
- `metrics`: Danh sách các metrics cần lấy (List[str])
- `dimensions`: Danh sách các dimensions để phân tích (Optional[List[str]])

**Ví dụ:**

```python
metrics_filter = MetricsFilter(
    date_range=DateRange(
        start_date=datetime(2023, 1,.1),
        end_date=datetime(2023, 1, 31)
    ),
    metrics=["impressions", "clicks", "ctr"],
    dimensions=["campaign", "date"]
)
```

## Response Models

### BaseResponse

`BaseResponse` là model cơ bản cho tất cả API responses.

```python
class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
```

**Properties:**

- `success`: Trạng thái request (bool, default: True)
- `message`: Message mô tả kết quả (Optional[str], default: None)

### PaginatedResponse

`PaginatedResponse` là model mở rộng từ BaseResponse, thêm thông tin phân trang.

```python
class PaginatedResponse(BaseResponse):
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[Any]
```

**Properties:**

- `total`: Tổng số items (int)
- `page`: Trang hiện tại (int)
- `page_size`: Số items trên mỗi trang (int)
- `total_pages`: Tổng số trang (int)
- `data`: Dữ liệu được phân trang (List[Any])

### MetricsResponse

`MetricsResponse` là model mở rộng từ BaseResponse, dùng cho các API endpoints trả về metrics data.

```python
class MetricsResponse(BaseResponse):
    data: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None
```

**Properties:**

- `data`: List các metrics data points (List[Dict[str, Any]])
- `summary`: Tóm tắt metrics (Optional[Dict[str, Any]], default: None)

## Pagination Parameters

`PaginationParams` là model dùng để xử lý phân trang trong các API endpoints.

```python
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
```

**Properties:**

- `page`: Số trang hiện tại, bắt đầu từ 1 (int, default: 1)
- `page_size`: Số items trên mỗi trang (int, default: 20, max: 100)

## Usage

### Import Models

```python
from app.models import (
    DateRange,
    MetricsFilter,
    PaginationParams,
    BaseResponse,
    PaginatedResponse,
    MetricsResponse
)
```

### Sử dụng trong API Endpoints

```python
@router.get("/facebook/campaigns", response_model=PaginatedResponse)
async def get_facebook_campaigns(
    pagination: PaginationParams = Depends(),
    date_range: Optional[DateRange] = None
):
    # Implement logic
    pass

@router.get("/facebook/campaigns/{campaign_id}/metrics", response_model=MetricsResponse)
async def get_facebook_campaign_metrics(
    campaign_id: str,
    filter: MetricsFilter
):
    # Implement logic
    pass
```
