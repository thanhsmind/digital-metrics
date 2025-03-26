import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from facebook_business.adobjects.business import Business
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.post import Post
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError

from app.core.config import settings
from app.models.facebook import (
    BusinessPage,
    PageToken,
    PostInsight,
    TokenDebugInfo,
    VideoInsight,
)


class FacebookApiManager:
    def __init__(self):
        self.app_id = settings.FACEBOOK_APP_ID
        self.app_secret = settings.FACEBOOK_APP_SECRET
        self.access_token = settings.FACEBOOK_ACCESS_TOKEN
        self.api_version = settings.FACEBOOK_API_VERSION
        self.api = None
        self.init_api()

    def init_api(self):
        """Initialize Facebook API with credentials"""
        try:
            self.api = FacebookAdsApi.init(
                app_id=self.app_id,
                app_secret=self.app_secret,
                access_token=self.access_token,
                api_version=self.api_version,
            )
            FacebookAdsApi.set_default_api(self.api)
        except Exception as e:
            logging.error(f"Failed to initialize Facebook API: {str(e)}")
            raise

    async def get_business_post_insights(
        self,
        business_id: str,
        metrics: List[str],
        since_date: str,
        until_date: str,
    ) -> List[PostInsight]:
        """Get insights for all posts from all pages in a business"""
        try:
            business = Business(business_id)
            owned_pages = business.get_owned_pages()
            all_insights = []

            for page in owned_pages:
                posts = await self.get_all_posts(
                    page["id"], since_date, until_date
                )
                for post in posts:
                    insights = await self.get_post_insights(
                        page["id"], post["id"], metrics, since_date, until_date
                    )
                    if insights:
                        post_type = self.determine_post_type(post)
                        insight = PostInsight(
                            post_id=post["id"],
                            created_time=datetime.strptime(
                                post["created_time"], "%Y-%m-%dT%H:%M:%S%z"
                            ),
                            message=post.get("message"),
                            type=post_type,
                            metrics=insights,
                        )
                        all_insights.append(insight)

            return all_insights
        except FacebookRequestError as e:
            logging.error(f"Facebook API error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Error getting business post insights: {str(e)}")
            raise

    async def get_post_insights(
        self,
        page_id: str,
        post_id: str,
        metrics: List[str],
        since_date: str,
        until_date: str,
    ) -> Dict[str, Any]:
        """Get insights for a specific post"""
        try:
            post = Post(f"{page_id}_{post_id}")
            insights = post.get_insights(
                params={
                    "metric": metrics,
                    "since": since_date,
                    "until": until_date,
                }
            )

            results = {}
            for insight in insights:
                metric_name = insight["name"]
                if "values" in insight and len(insight["values"]) > 0:
                    results[metric_name] = insight["values"][0]["value"]
                else:
                    results[metric_name] = 0

            return results
        except FacebookRequestError as e:
            logging.error(f"Facebook API error getting post insights: {str(e)}")
            return {}
        except Exception as e:
            logging.error(f"Error getting post insights: {str(e)}")
            return {}

    def determine_post_type(self, post_data: Dict[str, Any]) -> str:
        """Determine the type of a post"""
        if "type" not in post_data:
            return "unknown"

        post_type = post_data["type"]
        if post_type == "video":
            if "is_reel" in post_data and post_data["is_reel"]:
                return "reel"
        return post_type

    async def get_business_pages(self, business_id: str) -> List[BusinessPage]:
        """Get all pages owned by a business"""
        try:
            business = Business(business_id)
            owned_pages = business.get_owned_pages()
            pages = []

            for page in owned_pages:
                has_insights = await self.test_insights_access(
                    page["access_token"], page["id"]
                )
                page_info = BusinessPage(
                    id=page["id"],
                    name=page["name"],
                    access_token=page["access_token"],
                    category=page.get("category"),
                    has_insights_access=has_insights,
                )
                pages.append(page_info)

            return pages
        except FacebookRequestError as e:
            logging.error(
                f"Facebook API error getting business pages: {str(e)}"
            )
            raise
        except Exception as e:
            logging.error(f"Error getting business pages: {str(e)}")
            raise

    async def test_insights_access(self, token: str, page_id: str) -> bool:
        """Test if we have insights access for a page"""
        try:
            page = Page(page_id)
            page.api_get(fields=["insights"])
            return True
        except:
            return False

    async def debug_token(self, token: str) -> TokenDebugInfo:
        """Debug a Facebook access token"""
        try:
            debug_info = self.api.debug_token(token)
            return TokenDebugInfo(
                app_id=debug_info["app_id"],
                application=debug_info["application"],
                expires_at=(
                    datetime.fromtimestamp(debug_info["expires_at"])
                    if debug_info.get("expires_at")
                    else None
                ),
                is_valid=debug_info["is_valid"],
                scopes=debug_info["scopes"],
                user_id=debug_info["user_id"],
            )
        except Exception as e:
            logging.error(f"Error debugging token: {str(e)}")
            raise
