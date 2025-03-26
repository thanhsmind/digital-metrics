from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.core import DateRange


class PageToken(BaseModel):
    page_id: str
    page_name: str
    access_token: str
    last_updated: str


class PostInsight(BaseModel):
    post_id: str
    created_time: datetime
    message: Optional[str]
    type: str
    metrics: Dict[str, Any]


class VideoInsight(BaseModel):
    video_id: str
    title: Optional[str]
    description: Optional[str]
    created_time: datetime
    metrics: Dict[str, Any]


class AdsInsight(BaseModel):
    account_id: str
    campaign_id: Optional[str]
    campaign_name: Optional[str]
    adset_id: Optional[str]
    adset_name: Optional[str]
    ad_id: Optional[str]
    ad_name: Optional[str]
    metrics: Dict[str, Any]
    dimensions: Dict[str, Any]


class TokenDebugInfo(BaseModel):
    app_id: str
    application: str
    expires_at: Optional[datetime]
    is_valid: bool
    scopes: List[str]
    user_id: str


class BusinessPage(BaseModel):
    id: str
    name: str
    access_token: str
    category: Optional[str]
    has_insights_access: bool


class FacebookMetricsRequest(BaseModel):
    """
    Model yêu cầu cho Facebook Metrics API.

    Attributes:
        page_id: ID của trang Facebook
        date_range: Khoảng thời gian cho metrics
        metrics: Danh sách các metrics cần lấy
        dimensions: Danh sách các dimensions để phân tích (optional)
    """

    page_id: str
    date_range: DateRange
    metrics: List[str]
    dimensions: Optional[List[str]] = None


class FacebookMetricsResponse(BaseModel):
    """
    Model phản hồi cho Facebook Metrics API.

    Attributes:
        success: Trạng thái của request
        message: Thông báo mô tả kết quả
        data: Dữ liệu metrics
        summary: Tóm tắt metrics (nếu có)
    """

    success: bool = True
    message: Optional[str] = None
    data: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None
