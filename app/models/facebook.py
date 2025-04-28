from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.common import DateRange


class PageToken(BaseModel):
    page_id: str
    page_name: str
    access_token: str
    last_updated: str


class PostInsight(BaseModel):
    """
    Represents insights data for a specific Facebook Page Post.

    Attributes:
        post_id: The ID of the post (usually in format pageid_postid).
        created_time: The datetime when the post was created.
        message: The text content of the post, if any.
        type: The type of the post (e.g., 'status', 'photo', 'video').
        metrics: A dictionary containing the requested metric values for the post.
    """

    post_id: str
    created_time: datetime
    message: Optional[str] = None
    type: str
    metrics: Dict[str, Any]

    model_config = {
        "json_schema_extra": {
            "example": {
                "post_id": "123456789_987654321",
                "created_time": "2023-10-15T10:30:00+0000",
                "message": "Check out our new blog post!",
                "type": "link",
                "metrics": {
                    "post_impressions": 5000,
                    "post_reach": 4500,
                    "post_engaged_users": 250,
                    "post_clicks": 150,
                },
            }
        }
    }


class VideoInsight(BaseModel):
    """
    Represents insights data for a specific Facebook Page Video (including Reels).

    Attributes:
        video_id: The ID of the video/reel.
        title: The title of the video, if any.
        description: The description of the video, if any.
        created_time: The datetime when the video was published.
        metrics: A dictionary containing the requested metric values for the video.
    """

    video_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    created_time: datetime
    metrics: Dict[str, Any]

    model_config = {
        "json_schema_extra": {
            "example": {
                "video_id": "123456789012345",
                "title": "My Awesome Reel",
                "description": "Check out this cool effect! #reel #effect",
                "created_time": "2023-11-01T18:00:00+0000",
                "metrics": {
                    "total_video_views": 15000,
                    "total_video_avg_watch_time": 8500,  # Milliseconds
                    "total_video_impressions": 25000,
                    "video_views_unique": 12000,
                },
            }
        }
    }


class AdsInsight(BaseModel):
    """
    Represents insights data for a Facebook Ad, AdSet, or Campaign.

    This model captures common identifiers and uses dictionaries for flexible
    storage of metrics and dimensions returned by the Facebook Ads API.

    Attributes:
        account_id: The ID of the ad account.
        campaign_id: The ID of the campaign (optional).
        campaign_name: The name of the campaign (optional).
        adset_id: The ID of the ad set (optional).
        adset_name: The name of the ad set (optional).
        ad_id: The ID of the ad (optional).
        ad_name: The name of the ad (optional).
        date_start: The start date of the insight data window (YYYY-MM-DD string).
        date_stop: The end date of the insight data window (YYYY-MM-DD string).
        metrics: A dictionary containing the requested metric values (e.g., {'impressions': 1000, 'spend': 12.34}).
        dimensions: A dictionary containing the breakdown dimensions (e.g., {'age': '25-34', 'gender': 'female'}).
    """

    account_id: str
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None
    adset_id: Optional[str] = None
    adset_name: Optional[str] = None
    ad_id: Optional[str] = None
    ad_name: Optional[str] = None
    date_start: Optional[str] = (
        None  # Dates are often returned as strings by FB API
    )
    date_stop: Optional[str] = None
    metrics: Dict[str, Any]
    dimensions: Dict[str, Any]

    model_config = {
        "json_schema_extra": {
            "example": {
                "account_id": "act_123456789",
                "campaign_id": "987654321",
                "campaign_name": "Awareness Campaign",
                "adset_id": "1122334455",
                "adset_name": "Lookalike Audience US",
                "ad_id": "5566778899",
                "ad_name": "Video Ad - Variant A",
                "date_start": "2023-10-01",
                "date_stop": "2023-10-31",
                "metrics": {
                    "impressions": 15000,
                    "reach": 12000,
                    "spend": 250.75,
                    "clicks": 300,
                    "ctr": 2.0,
                    "cpc": 0.84,
                },
                "dimensions": {
                    "publisher_platform": "facebook",
                    "device_platform": "mobile",
                },
            }
        }
    }


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


class FacebookCampaignMetricsRequest(BaseModel):
    """
    Model yêu cầu cho Facebook Campaign Metrics API.

    Attributes:
        ad_account_id: ID của tài khoản quảng cáo
        campaign_ids: Danh sách ID chiến dịch cần lấy metrics (optional)
        date_range: Khoảng thời gian cho metrics
        metrics: Danh sách các metrics cần lấy
        dimensions: Danh sách các dimensions để phân tích (optional)
    """

    ad_account_id: str
    campaign_ids: Optional[List[str]] = None
    date_range: DateRange
    metrics: List[str]
    dimensions: Optional[List[str]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "ad_account_id": "act_1234567890",
                "campaign_ids": ["987654321", "123123123"],
                "date_range": {
                    "start_date": "2023-11-01",
                    "end_date": "2023-11-30",
                },
                "metrics": ["impressions", "spend", "clicks", "actions"],
                "dimensions": ["age", "gender"],
            },
            "example_minimal": {
                "ad_account_id": "act_1234567890",
                "date_range": {
                    "start_date": "2023-11-01",
                    "end_date": "2023-11-30",
                },
                "metrics": ["impressions", "spend"],
            },
        }
    }


class FacebookMetricsResponse(BaseModel):
    """
    Model kết quả cho Facebook Metrics API.

    Attributes:
        success: Kết quả API là thành công hay thất bại
        message: Thông báo từ API
        data: Dữ liệu metrics (nếu thành công)
        summary: Tóm tắt metrics (nếu có)
    """

    success: bool
    message: str
    data: List[Dict[str, Any]]
    summary: Dict[str, Any] = {}

    model_config = {
        "json_schema_extra": {
            "example_success": {
                "success": True,
                "message": "Successfully retrieved 2 campaign insights.",
                "data": [
                    {
                        "account_id": "act_123",
                        "campaign_id": "c1",
                        "campaign_name": "Campaign 1",
                        "date_start": "2023-11-01",
                        "date_stop": "2023-11-30",
                        "metrics": {"impressions": 1000, "spend": 50.0},
                        "dimensions": {},
                    },
                    {
                        "account_id": "act_123",
                        "campaign_id": "c2",
                        "campaign_name": "Campaign 2",
                        "date_start": "2023-11-01",
                        "date_stop": "2023-11-30",
                        "metrics": {"impressions": 2000, "spend": 100.0},
                        "dimensions": {},
                    },
                ],
                "summary": {"total_impressions": 3000, "total_spend": 150.0},
            },
            "example_error": {
                "success": False,
                "message": "Invalid metrics requested: [invalid_metric]",
                "data": [],
                "summary": {},
            },
        }
    }
