from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.core import DateRange


class CampaignInsight(BaseModel):
    client_id: str
    campaign_id: str
    campaign_name: str
    metrics: Dict[str, Any]
    dimensions: Dict[str, Any]
    date_range: str


class AdGroupInsight(BaseModel):
    client_id: str
    campaign_id: str
    campaign_name: str
    ad_group_id: str
    ad_group_name: str
    metrics: Dict[str, Any]
    dimensions: Dict[str, Any]
    date_range: str


class AdInsight(BaseModel):
    client_id: str
    campaign_id: str
    campaign_name: str
    ad_group_id: str
    ad_group_name: str
    ad_id: str
    ad_name: str
    metrics: Dict[str, Any]
    dimensions: Dict[str, Any]
    date_range: str


class GoogleAdsConfig(BaseModel):
    developer_token: str
    client_id: str
    client_secret: str
    refresh_token: str
    login_customer_id: Optional[str]
    use_proto_plus: bool = True


class GoogleMetricsRequest(BaseModel):
    """
    Model yêu cầu cho Google Ads Metrics API.

    Attributes:
        client_id: ID của client Google
        date_range: Khoảng thời gian cho metrics
        metrics: Danh sách các metrics cần lấy
        dimensions: Danh sách các dimensions để phân tích (optional)
    """

    client_id: str
    date_range: DateRange
    metrics: List[str]
    dimensions: Optional[List[str]] = None


class AdGroupPerformance(BaseModel):
    """
    Model hiệu suất của nhóm quảng cáo Google Ads.

    Attributes:
        ad_group_id: ID của nhóm quảng cáo
        ad_group_name: Tên của nhóm quảng cáo
        campaign_id: ID của chiến dịch
        campaign_name: Tên của chiến dịch
        metrics: Các chỉ số hiệu suất
    """

    ad_group_id: str
    ad_group_name: str
    campaign_id: str
    campaign_name: str
    metrics: Dict[str, Any]


class CampaignPerformance(BaseModel):
    """
    Model hiệu suất của chiến dịch Google Ads.

    Attributes:
        campaign_id: ID của chiến dịch
        campaign_name: Tên của chiến dịch
        metrics: Các chỉ số hiệu suất
    """

    campaign_id: str
    campaign_name: str
    metrics: Dict[str, Any]


class GoogleAdsReport(BaseModel):
    """
    Model báo cáo tổng hợp từ Google Ads.

    Attributes:
        campaigns: Danh sách các chiến dịch
        ad_groups: Danh sách các nhóm quảng cáo
        time_range: Khoảng thời gian của báo cáo
    """

    campaigns: List[CampaignPerformance]
    ad_groups: List[AdGroupPerformance]
    time_range: str
