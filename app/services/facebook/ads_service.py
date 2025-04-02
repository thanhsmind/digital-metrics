import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.post import Post
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError

from app.core.config import settings
from app.models.date import DateRange
from app.services.facebook.auth_service import FacebookAuthService


class FacebookAdsService:
    """Service để lấy metrics từ Facebook Ads API"""

    def __init__(self):
        """Khởi tạo service với credentials từ environment"""
        self.app_id = settings.FACEBOOK_APP_ID
        self.app_secret = settings.FACEBOOK_APP_SECRET
        self.api_version = settings.FACEBOOK_API_VERSION
        self.auth_service = FacebookAuthService()

    async def initialize(self, access_token: str):
        """
        Khởi tạo Facebook Ads API với access token

        Args:
            access_token: Facebook access token

        Returns:
            Self để có thể chain methods
        """
        # Khởi tạo API
        FacebookAdsApi.init(
            app_id=self.app_id,
            app_secret=self.app_secret,
            access_token=access_token,
            api_version=self.api_version,
        )
        return self

    async def get_campaign_metrics(
        self,
        ad_account_id: str,
        campaign_ids: List[str],
        date_range: DateRange,
        metrics: List[str],
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Lấy metrics của campaigns từ Facebook Ads

        Args:
            ad_account_id: ID của ad account
            campaign_ids: List các campaign IDs cần lấy metrics
            date_range: Khoảng thời gian cần lấy metrics
            metrics: List các metrics cần lấy
            access_token: Facebook access token

        Returns:
            Dict chứa metrics data và summary

        Raises:
            FacebookRequestError: Khi có lỗi từ Facebook API
        """
        try:
            # Khởi tạo API với access token
            await self.initialize(access_token)

            # Chuẩn bị parameters
            params = {
                "time_range": {
                    "since": date_range.start_date.strftime("%Y-%m-%d"),
                    "until": date_range.end_date.strftime("%Y-%m-%d"),
                },
                "fields": metrics,
            }

            # Nếu có campaign_ids, thêm filter
            if campaign_ids:
                params["filtering"] = [
                    {
                        "field": "campaign.id",
                        "operator": "IN",
                        "value": campaign_ids,
                    }
                ]

            # Lấy AdAccount object
            account = AdAccount(f"act_{ad_account_id}")

            # Lấy Insights
            insights = account.get_insights(
                params=params,
            )

            # Xử lý kết quả
            result = []
            for insight in insights:
                result.append(insight.export_all_data())

            # Tạo summary bằng cách tính tổng các metrics
            summary = {}
            if result:
                for metric in metrics:
                    if metric in result[0]:
                        try:
                            # Chỉ tính tổng cho numeric metrics
                            values = [
                                float(item.get(metric, 0))
                                for item in result
                                if metric in item
                            ]
                            if values:
                                summary[metric] = sum(values)
                        except (ValueError, TypeError):
                            # Bỏ qua nếu metric không phải số
                            pass

            return {
                "data": result,
                "summary": summary,
                "pagination": {
                    "has_more": len(insights) > 0 and insights.has_next_page(),
                },
            }

        except FacebookRequestError as e:
            logging.error(
                f"Facebook API error during getting campaign metrics: {str(e)}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error during getting campaign metrics: {str(e)}")
            raise e

    async def get_post_metrics(
        self,
        page_id: str,
        post_ids: Optional[List[str]],
        date_range: DateRange,
        metrics: List[str],
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Lấy metrics của posts từ Facebook

        Args:
            page_id: ID của trang Facebook
            post_ids: List các post IDs cần lấy metrics (optional)
            date_range: Khoảng thời gian cần lấy metrics
            metrics: List các metrics cần lấy
            access_token: Facebook access token

        Returns:
            Dict chứa metrics data và summary

        Raises:
            FacebookRequestError: Khi có lỗi từ Facebook API
        """
        try:
            # Khởi tạo API với access token
            await self.initialize(access_token)
            
            # Lấy page object
            page = Page(page_id)
            
            # Lấy posts từ page
            if post_ids:
                posts = []
                for post_id in post_ids:
                    try:
                        post = Post(f"{page_id}_{post_id}")
                        post_data = post.api_get(
                            fields=["id", "message", "created_time", "type"]
                        )
                        posts.append(post_data)
                    except FacebookRequestError as e:
                        logging.warning(f"Could not get post {post_id}: {str(e)}")
            else:
                # Lấy tất cả posts trong khoảng thời gian
                posts = page.get_posts(
                    params={
                        "since": date_range.start_date.strftime("%Y-%m-%d"),
                        "until": date_range.end_date.strftime("%Y-%m-%d"),
                        "fields": ["id", "message", "created_time", "type"],
                    }
                )
            
            # Kết quả chứa thông tin post và metrics
            result = []
            
            # Lấy insights cho từng post
            for post in posts:
                post_data = post.export_all_data() if hasattr(post, "export_all_data") else post
                post_id = post_data["id"].split("_")[-1]  # Extract post_id from page_id_post_id
                
                try:
                    # Lấy post object
                    post_obj = Post(post_data["id"])
                    
                    # Lấy insights
                    insights = post_obj.get_insights(
                        params={
                            "metric": metrics,
                            "since": date_range.start_date.strftime("%Y-%m-%d"),
                            "until": date_range.end_date.strftime("%Y-%m-%d"),
                        }
                    )
                    
                    # Xử lý kết quả insights
                    metrics_data = {}
                    for insight in insights:
                        metric_name = insight["name"]
                        if "values" in insight and len(insight["values"]) > 0:
                            metrics_data[metric_name] = insight["values"][0]["value"]
                        else:
                            metrics_data[metric_name] = 0
                    
                    # Tạo post data với metrics
                    post_with_metrics = {
                        "post_id": post_id,
                        "page_id": page_id,
                        "message": post_data.get("message", ""),
                        "created_time": post_data.get("created_time", ""),
                        "type": post_data.get("type", "unknown"),
                    }
                    
                    # Thêm metrics vào post data
                    for metric, value in metrics_data.items():
                        post_with_metrics[metric] = value
                    
                    result.append(post_with_metrics)
                except FacebookRequestError as e:
                    logging.warning(f"Could not get insights for post {post_id}: {str(e)}")
                except Exception as e:
                    logging.warning(f"Error processing post {post_id}: {str(e)}")
            
            # Tạo summary bằng cách tính tổng các metrics
            summary = {}
            if result:
                for metric in metrics:
                    values = []
                    for item in result:
                        if metric in item:
                            try:
                                # Chỉ tính tổng cho numeric metrics
                                value = float(item.get(metric, 0))
                                values.append(value)
                            except (ValueError, TypeError):
                                # Bỏ qua nếu metric không phải số
                                pass
                    if values:
                        summary[metric] = sum(values)
            
            return {
                "data": result,
                "summary": summary,
                "pagination": {
                    "has_more": False,  # Currently not supporting pagination for posts
                },
            }

        except FacebookRequestError as e:
            logging.error(
                f"Facebook API error during getting post metrics: {str(e)}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error during getting post metrics: {str(e)}")
            raise e

    async def get_reel_metrics(
        self,
        page_id: str,
        reel_ids: Optional[List[str]],
        date_range: DateRange,
        metrics: List[str],
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Lấy metrics của reels từ Facebook

        Args:
            page_id: ID của trang Facebook
            reel_ids: List các reel IDs cần lấy metrics (optional)
            date_range: Khoảng thời gian cần lấy metrics
            metrics: List các metrics cần lấy
            access_token: Facebook access token

        Returns:
            Dict chứa metrics data và summary

        Raises:
            FacebookRequestError: Khi có lỗi từ Facebook API
        """
        try:
            # Khởi tạo API với access token
            await self.initialize(access_token)
            
            # Lấy page object
            page = Page(page_id)
            
            # Lấy reels từ page
            # Reels are a type of video post in Facebook, so we need to get all video posts
            # and filter for those that are reels
            if reel_ids:
                reels = []
                for reel_id in reel_ids:
                    try:
                        reel = Post(f"{page_id}_{reel_id}")
                        reel_data = reel.api_get(
                            fields=["id", "message", "created_time", "type", "is_reel"]
                        )
                        if reel_data.get("is_reel", False) or reel_data.get("type") == "video":
                            reels.append(reel_data)
                    except FacebookRequestError as e:
                        logging.warning(f"Could not get reel {reel_id}: {str(e)}")
            else:
                # Lấy tất cả video posts trong khoảng thời gian
                video_posts = page.get_posts(
                    params={
                        "since": date_range.start_date.strftime("%Y-%m-%d"),
                        "until": date_range.end_date.strftime("%Y-%m-%d"),
                        "fields": ["id", "message", "created_time", "type", "is_reel"],
                        "limit": 100,  # Increase limit to get more posts
                    }
                )
                
                # Filter for reels
                reels = []
                for post in video_posts:
                    post_data = post.export_all_data() if hasattr(post, "export_all_data") else post
                    if post_data.get("is_reel", False) or (post_data.get("type") == "video"):
                        reels.append(post_data)
            
            # Kết quả chứa thông tin reel và metrics
            result = []
            
            # Lấy insights cho từng reel
            for reel in reels:
                reel_data = reel.export_all_data() if hasattr(reel, "export_all_data") else reel
                reel_id = reel_data["id"].split("_")[-1]  # Extract reel_id from page_id_reel_id
                
                try:
                    # Lấy post object
                    reel_obj = Post(reel_data["id"])
                    
                    # Lấy insights
                    insights = reel_obj.get_insights(
                        params={
                            "metric": metrics,
                            "since": date_range.start_date.strftime("%Y-%m-%d"),
                            "until": date_range.end_date.strftime("%Y-%m-%d"),
                        }
                    )
                    
                    # Xử lý kết quả insights
                    metrics_data = {}
                    for insight in insights:
                        metric_name = insight["name"]
                        if "values" in insight and len(insight["values"]) > 0:
                            # For reaction metrics which might be returned as a dictionary
                            if isinstance(insight["values"][0]["value"], dict):
                                for reaction_type, count in insight["values"][0]["value"].items():
                                    metrics_data[f"{metric_name}_{reaction_type}"] = count
                            else:
                                metrics_data[metric_name] = insight["values"][0]["value"]
                        else:
                            metrics_data[metric_name] = 0
                    
                    # Tạo reel data với metrics
                    reel_with_metrics = {
                        "reel_id": reel_id,
                        "page_id": page_id,
                        "message": reel_data.get("message", ""),
                        "created_time": reel_data.get("created_time", ""),
                        "type": "reel",
                    }
                    
                    # Thêm metrics vào reel data
                    for metric, value in metrics_data.items():
                        reel_with_metrics[metric] = value
                    
                    result.append(reel_with_metrics)
                except FacebookRequestError as e:
                    logging.warning(f"Could not get insights for reel {reel_id}: {str(e)}")
                except Exception as e:
                    logging.warning(f"Error processing reel {reel_id}: {str(e)}")
            
            # Tạo summary bằng cách tính tổng các metrics
            summary = {}
            if result:
                # Find all metric keys across all results
                all_metric_keys = set()
                for item in result:
                    for key in item.keys():
                        if key not in ["reel_id", "page_id", "message", "created_time", "type"]:
                            all_metric_keys.add(key)
                
                # Calculate summary for each metric
                for metric in all_metric_keys:
                    values = []
                    for item in result:
                        if metric in item:
                            try:
                                # Only sum numeric metrics
                                value = float(item.get(metric, 0))
                                values.append(value)
                            except (ValueError, TypeError):
                                # Skip if metric is not a number
                                pass
                    if values:
                        summary[metric] = sum(values)
            
            return {
                "data": result,
                "summary": summary,
                "pagination": {
                    "has_more": False,  # Currently not supporting pagination for reels
                },
            }

        except FacebookRequestError as e:
            logging.error(
                f"Facebook API error during getting reel metrics: {str(e)}"
            )
            raise e
        except Exception as e:
            logging.error(f"Error during getting reel metrics: {str(e)}")
            raise e
