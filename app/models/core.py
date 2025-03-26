from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class DateRange(BaseModel):
    """
    Đại diện cho một khoảng thời gian trong báo cáo metrics.

    Attributes:
        start_date: Ngày bắt đầu của khoảng thời gian
        end_date: Ngày kết thúc của khoảng thời gian
    """

    start_date: datetime
    end_date: datetime

    @field_validator("end_date")
    def validate_date_range(cls, end_date, info):
        """Kiểm tra end_date phải sau start_date."""
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date phải sau start_date")
        return end_date


class MetricsFilter(BaseModel):
    """
    Model dùng để lọc và phân tích metrics.

    Attributes:
        date_range: Khoảng thời gian cho metrics
        metrics: Danh sách các metrics cần lấy
        dimensions: Danh sách các dimensions để phân tích (optional)
    """

    date_range: DateRange
    metrics: List[str]
    dimensions: Optional[List[str]] = None


class PaginationParams(BaseModel):
    """
    Tham số phân trang cho các API endpoints.

    Attributes:
        page: Số trang hiện tại, bắt đầu từ 1
        page_size: Số items trên mỗi trang
    """

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class BaseResponse(BaseModel):
    """
    Base response model cho tất cả API endpoints.

    Attributes:
        success: Trạng thái request
        message: Message mô tả kết quả
    """

    success: bool = True
    message: Optional[str] = None


class PaginatedResponse(BaseResponse):
    """
    Response model với phân trang.

    Attributes:
        total: Tổng số items
        page: Trang hiện tại
        page_size: Số items trên mỗi trang
        total_pages: Tổng số trang
        data: Dữ liệu được phân trang
    """

    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[Any]


class MetricsResponse(BaseResponse):
    """
    Response model cho metrics data.

    Attributes:
        data: List các metrics data points
        summary: Tóm tắt metrics (aggregated)
    """

    data: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None


class SortParams(BaseModel):
    """
    Tham số sắp xếp cho các API endpoints.

    Attributes:
        sort_by: Trường dùng để sắp xếp
        sort_order: Thứ tự sắp xếp (asc hoặc desc)
    """

    sort_by: str
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")
