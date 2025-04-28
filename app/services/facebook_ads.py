import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.pagepost import PagePost

# Comment out the problematic import temporarily
# from facebook_business.adobjects.video import Video
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError

from app.core.config import settings
from app.models.common import DateRange
from app.models.facebook import (
    AdsInsight,
    BusinessPage,
    FacebookCampaignMetricsRequest,
    PostInsight,
    TokenDebugInfo,
    VideoInsight,
)
from app.services.cache_service import CacheService
from app.utils.encryption import TokenEncryption
from app.utils.error_handler import FacebookErrorHandler
from app.utils.helpers import generate_cache_key

logger = logging.getLogger(__name__)

DEFAULT_CACHE_TTL = 3600  # 1 hour


# Temporary Video class replacement
class Video:
    """Temporary replacement for facebook_business.adobjects.video.Video"""

    class Field:
        """Field definitions for Video object"""

        id = "id"
        title = "title"
        description = "description"
        created_time = "created_time"

    def __init__(self, fbid, api=None):
        """Initialize Video object"""
        self.fbid = fbid
        self.api = api

    def get_insights(self, fields=None, params=None):
        """Get insights for this video"""
        if not fields:
            fields = []
        if not params:
            params = {}

        path = f"{self.fbid}/insights"
        if self.api:
            return self.api.call("GET", path, params=params, fields=fields)
        return []


class FacebookAdsService:
    """
    Service class for interacting with the Facebook Ads API.

    Handles authentication, making API calls, and processing responses
    for campaign, post, and reel insights.
    """

    def __init__(self, cache_service: CacheService):
        """
        Initializes the FacebookAdsService.

        Args:
            cache_service: An instance of CacheService for caching results.
        """
        # Initialization with default app ID and secret might be needed
        # if not relying on a globally initialized API instance.
        # FacebookAdsApi.init(
        #     app_id=settings.FACEBOOK_APP_ID,
        #     app_secret=settings.FACEBOOK_APP_SECRET,
        #     access_token=settings.FACEBOOK_ACCESS_TOKEN, # A system token or default
        #     api_version=settings.FACEBOOK_API_VERSION,
        # )
        self.cache_service = cache_service
        self.error_handler = FacebookErrorHandler()
        self.default_token = (
            None  # Default token được set thông qua dependency injection
        )
        logger.info("FacebookAdsService initialized.")

    async def _get_api_instance(self, access_token: str) -> FacebookAdsApi:
        """Initializes the FacebookAdsApi instance with a specific user token."""
        # Decrypt token if necessary (using TokenEncryption)
        # decrypted_token = TokenEncryption.decrypt_token(access_token)
        decrypted_token = access_token  # Placeholder if not encrypted
        return FacebookAdsApi.init(
            app_id=settings.FACEBOOK_APP_ID,
            app_secret=settings.FACEBOOK_APP_SECRET,
            access_token=decrypted_token,
            api_version=settings.FACEBOOK_API_VERSION,
        )

    def update_access_token(self, access_token: str) -> None:
        """
        Updates the access token used by the service for API calls.

        Args:
            access_token: The Facebook access token to use for API calls
        """
        logger.debug("Updating service access token")
        if access_token:
            # If token is encrypted, it will be decrypted when used in _get_api_instance
            self.default_token = access_token
        else:
            logger.warning("Attempted to set empty access token, ignoring")

    async def get_campaign_insights(
        self,
        request: FacebookCampaignMetricsRequest,
        access_token: str,
    ) -> List[AdsInsight]:
        """
        Fetches campaign-level insights from the Facebook Ads API.
        Handles caching and pagination.

        Args:
            request: The request object containing parameters like account ID, date range, metrics.
            access_token: The user's Facebook access token.

        Returns:
            A list of AdsInsight objects containing the campaign metrics.

        Raises:
            ApplicationError: For API errors or processing issues.
        """
        logger.info(
            f"Fetching campaign insights for account: {request.ad_account_id} "
            f"Metrics: {request.metrics}, Dimensions: {request.dimensions}"
        )

        # 1. Cache Check
        # Include dimensions and campaign_ids in cache key if they exist
        cache_key_params = {
            "account_id": request.ad_account_id,
            "start_date": request.date_range.start_date.isoformat(),
            "end_date": request.date_range.end_date.isoformat(),
            "metrics": sorted(request.metrics),
            "dimensions": (
                sorted(request.dimensions) if request.dimensions else None
            ),
            "campaign_ids": (
                sorted(request.campaign_ids) if request.campaign_ids else None
            ),
            "level": "campaign",
        }
        cache_key = generate_cache_key("fb_campaign_insights", cache_key_params)
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            logger.info(
                f"Returning cached campaign insights for key: {cache_key}"
            )
            # Assuming cached data is stored as list of dicts, convert back to models
            try:
                return [AdsInsight(**item) for item in cached_data]
            except Exception as e:
                logger.warning(
                    f"Failed to parse cached data for key {cache_key}: {e}. Refetching."
                )

        insights_data = []
        try:
            # 2. Initialize API
            api = await self._get_api_instance(access_token)

            # 3. API Parameters
            fields_to_request = [
                AdsInsights.Field.campaign_id,
                AdsInsights.Field.campaign_name,
                AdsInsights.Field.account_id,
                AdsInsights.Field.date_start,
                AdsInsights.Field.date_stop,
            ]
            # Add requested metrics to fields
            fields_to_request.extend(request.metrics)
            # Dimensions are handled by 'breakdowns', not 'fields'

            params = {
                "level": "campaign",
                "time_range": {
                    "since": request.date_range.start_date.isoformat(),
                    "until": request.date_range.end_date.isoformat(),
                },
                "limit": 100,  # Adjust limit as needed
                # Action breakdowns are specified differently if needed
                # 'action_breakdowns': ['action_type']
            }

            if request.dimensions:
                # Filter out any dimensions that are actually metrics
                valid_dimensions = [
                    d for d in request.dimensions if d not in request.metrics
                ]
                if valid_dimensions:
                    params["breakdowns"] = valid_dimensions

            if request.campaign_ids:
                params["filtering"] = [
                    {
                        "field": "campaign.id",
                        "operator": "IN",
                        "value": request.campaign_ids,
                    }
                ]

            # 4. API Call & Pagination
            account = AdAccount(f"act_{request.ad_account_id}", api=api)
            insights_cursor = await asyncio.to_thread(
                account.get_insights, fields=fields_to_request, params=params
            )

            # Use execute_async to fetch all pages - consider memory for very large result sets
            all_insights = await asyncio.to_thread(
                list, insights_cursor
            )  # Convert cursor to list

            # 5. Process response into AdsInsight objects
            for insight in all_insights:
                insight_dict = insight.export_data()

                # Prepare metrics dict, converting numbers
                metrics_dict = {}
                for metric in request.metrics:
                    if metric in insight_dict:
                        try:
                            # Attempt to convert known numeric metrics
                            if metric in [
                                "impressions",
                                "reach",
                                "clicks",
                                "spend",
                                "frequency",
                                "cpm",
                                "cpc",
                                "ctr",
                            ]:
                                metrics_dict[metric] = (
                                    float(insight_dict[metric])
                                    if "." in str(insight_dict[metric])
                                    else int(insight_dict[metric])
                                )
                            else:  # Handle actions or other complex types if necessary
                                metrics_dict[metric] = insight_dict[metric]
                        except (ValueError, TypeError) as e:
                            logger.warning(
                                f"Could not convert metric '{metric}' value '{insight_dict[metric]}' to number: {e}. Keeping original."
                            )
                            metrics_dict[metric] = insight_dict[
                                metric
                            ]  # Keep original if conversion fails

                # Prepare dimensions dict (breakdowns are returned at top level)
                dimensions_dict = {}
                if request.dimensions:
                    for dim in request.dimensions:
                        if dim in insight_dict:
                            dimensions_dict[dim] = insight_dict[dim]

                ads_insight_data = {
                    "account_id": insight_dict.get(
                        AdsInsights.Field.account_id
                    ),
                    "campaign_id": insight_dict.get(
                        AdsInsights.Field.campaign_id
                    ),
                    "campaign_name": insight_dict.get(
                        AdsInsights.Field.campaign_name
                    ),
                    # Adset and Ad fields will be None at campaign level
                    "adset_id": None,
                    "adset_name": None,
                    "ad_id": None,
                    "ad_name": None,
                    "date_start": insight_dict.get(
                        AdsInsights.Field.date_start
                    ),
                    "date_stop": insight_dict.get(AdsInsights.Field.date_stop),
                    "metrics": metrics_dict,
                    "dimensions": dimensions_dict,
                }
                insights_data.append(AdsInsight(**ads_insight_data))

            # 6. Caching
            # Store as list of dicts for JSON compatibility
            await self.cache_service.set(
                cache_key,
                [item.dict() for item in insights_data],
                ttl=DEFAULT_CACHE_TTL,
            )
            logger.info(
                f"Cached {len(insights_data)} campaign insights for key: {cache_key}"
            )

        except FacebookRequestError as e:
            logger.error(
                f"Facebook API error fetching campaign insights: {e}",
                exc_info=True,
            )
            # Use error handler to potentially raise a more specific ApplicationError
            self.error_handler.handle_facebook_error(
                e,
                f"fetching campaign insights for account {request.ad_account_id}",
            )
            # Depending on handler's implementation, it might raise, so this return might not be reached
            return (
                []
            )  # Return empty list on handled API error if handler doesn't raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching campaign insights: {e}",
                exc_info=True,
            )
            # Raise a generic application error or re-raise
            # For now, return empty list, but ideally raise a classified error
            # raise ApplicationError(f"An unexpected error occurred: {e}") from e
            return []

        return insights_data

    async def get_post_insights(
        self,
        page_id: str,
        metrics: List[str],
        date_range: DateRange,
        access_token: str,
    ) -> List[PostInsight]:
        """
        Fetches post-level insights for a specific Facebook Page.

        Note: This implementation fetches posts within the date range first,
        then gets insights for each post individually. This can be slow
        for pages with many posts. Consider optimizing if performance is critical.

        Args:
            page_id: The ID of the Facebook Page.
            metrics: A list of post metrics to retrieve (e.g., ['post_impressions', 'post_clicks']).
            date_range: The date range for the insights.
            access_token: The Page access token.

        Returns:
            A list of PostInsight objects.

        Raises:
            ApplicationError: For API errors or processing issues.
        """
        logger.info(
            f"Fetching post insights for page: {page_id} Metrics: {metrics}"
        )

        # 1. Cache Check (Cache key based on page, metrics, date range)
        cache_key_params = {
            "page_id": page_id,
            "metrics": sorted(metrics),
            "start_date": date_range.start_date.isoformat(),
            "end_date": date_range.end_date.isoformat(),
        }
        cache_key = generate_cache_key("fb_post_insights", cache_key_params)
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached post insights for key: {cache_key}")
            try:
                return [PostInsight(**item) for item in cached_data]
            except Exception as e:
                logger.warning(
                    f"Failed to parse cached post data for key {cache_key}: {e}. Refetching."
                )

        post_insights_data = []
        try:
            # 2. Initialize API
            api = await self._get_api_instance(access_token)
            page = Page(page_id, api=api)

            # 3. Fetch Posts within Date Range
            # Convert dates to Unix timestamps for 'since' and 'until'
            since_timestamp = int(
                datetime.combine(
                    date_range.start_date, datetime.min.time()
                ).timestamp()
            )
            until_timestamp = int(
                datetime.combine(
                    date_range.end_date, datetime.max.time()
                ).timestamp()
            )

            post_fields = [
                PagePost.Field.id,
                PagePost.Field.created_time,
                PagePost.Field.message,
                PagePost.Field.type,
            ]
            post_params = {
                "since": since_timestamp,
                "until": until_timestamp,
                "limit": 100,  # Fetch posts in batches
            }

            logger.debug(
                f"Fetching posts for page {page_id} between {date_range.start_date} and {date_range.end_date}"
            )
            posts_cursor = await asyncio.to_thread(
                page.get_posts, fields=post_fields, params=post_params
            )
            all_posts = await asyncio.to_thread(list, posts_cursor)
            logger.info(
                f"Found {len(all_posts)} posts for page {page_id} in the specified date range."
            )

            # 4. Fetch Insights for Each Post
            insight_tasks = []
            post_details_map = {
                post[PagePost.Field.id]: post for post in all_posts
            }

            async def fetch_single_post_insights(post_id):
                try:
                    post = PagePost(post_id, api=api)
                    # Construct insight params - period 'lifetime' often used for post insights
                    insight_params = {
                        "metric": ",".join(metrics),
                        "period": "lifetime",  # Or 'day'/'week' etc. if needed
                    }
                    # Note: get_insights might be synchronous in SDK, wrap if needed
                    # insights_result = await asyncio.to_thread(post.get_insights, params=insight_params)
                    # Assuming get_insights IS async or can be called directly
                    insights_result = await asyncio.to_thread(
                        post.get_insights, params=insight_params
                    )

                    if insights_result:
                        # Insights for a post usually return a list with one item
                        insight_data = insights_result[0].export_data()
                        metrics_dict = {}
                        if "values" in insight_data:
                            for value_entry in insight_data["values"]:
                                metrics_dict[value_entry["verb"]] = (
                                    value_entry.get("value", 0)
                                )
                        # Alternative: sometimes metrics are direct keys
                        for metric_name in metrics:
                            if metric_name in insight_data:
                                metrics_dict[metric_name] = insight_data[
                                    metric_name
                                ]

                        post_detail = post_details_map.get(post_id)
                        if post_detail:
                            return PostInsight(
                                post_id=post_detail[PagePost.Field.id],
                                created_time=post_detail[
                                    PagePost.Field.created_time
                                ],
                                message=post_detail.get(PagePost.Field.message),
                                type=post_detail[PagePost.Field.type],
                                metrics=metrics_dict,
                            )
                except FacebookRequestError as e:
                    # Log error for specific post but continue with others
                    logger.warning(
                        f"FB API error fetching insights for post {post_id}: {e.message or e}"
                    )
                    self.error_handler.handle_facebook_error(
                        e,
                        f"fetching insights for post {post_id}",
                        raise_exception=False,
                    )
                except Exception as e:
                    logger.error(
                        f"Unexpected error fetching insights for post {post_id}: {e}",
                        exc_info=True,
                    )
                return None  # Return None on error for this post

            # Run insight fetching concurrently
            tasks = [
                fetch_single_post_insights(post_id)
                for post_id in post_details_map.keys()
            ]
            results = await asyncio.gather(*tasks)

            # Filter out None results (errors)
            post_insights_data = [res for res in results if res is not None]
            logger.info(
                f"Successfully fetched insights for {len(post_insights_data)} posts."
            )

            # 5. Caching
            await self.cache_service.set(
                cache_key,
                [item.dict() for item in post_insights_data],
                ttl=DEFAULT_CACHE_TTL,
            )
            logger.info(
                f"Cached {len(post_insights_data)} post insights for key: {cache_key}"
            )

        except FacebookRequestError as e:
            logger.error(
                f"Facebook API error fetching posts or insights for page {page_id}: {e}",
                exc_info=True,
            )
            self.error_handler.handle_facebook_error(
                e, f"fetching posts/insights for page {page_id}"
            )
            return []
        except Exception as e:
            logger.error(
                f"Unexpected error fetching post insights for page {page_id}: {e}",
                exc_info=True,
            )
            return []

        return post_insights_data

    async def get_reel_insights(
        self,
        page_id: str,
        metrics: List[str],
        date_range: DateRange,
        access_token: str,
    ) -> List[VideoInsight]:
        """
        Fetches reel insights for a specific Facebook Page.

        Note: This implementation fetches videos within the date range first,
        then gets insights for each video individually. Reels are a type of video.
        This can be slow for pages with many videos.

        Args:
            page_id: The ID of the Facebook Page.
            metrics: A list of video/reel metrics to retrieve (e.g., ['total_video_views']).
            date_range: The date range for filtering videos by creation time.
            access_token: The Page access token.

        Returns:
            A list of VideoInsight objects for Reels found in the date range.

        Raises:
            ApplicationError: For API errors or processing issues.
        """
        logger.info(
            f"Fetching reel insights for page: {page_id} Metrics: {metrics}"
        )

        # 1. Cache Check
        cache_key_params = {
            "page_id": page_id,
            "metrics": sorted(metrics),
            "start_date": date_range.start_date.isoformat(),
            "end_date": date_range.end_date.isoformat(),
            "type": "reel",  # Differentiate from generic video insights if needed
        }
        cache_key = generate_cache_key("fb_reel_insights", cache_key_params)
        cached_data = await self.cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached reel insights for key: {cache_key}")
            try:
                return [VideoInsight(**item) for item in cached_data]
            except Exception as e:
                logger.warning(
                    f"Failed to parse cached reel data for key {cache_key}: {e}. Refetching."
                )

        reel_insights_data = []
        try:
            # 2. Initialize API
            api = await self._get_api_instance(access_token)
            page = Page(page_id, api=api)

            # 3. Fetch Videos within Date Range
            since_timestamp = int(
                datetime.combine(
                    date_range.start_date, datetime.min.time()
                ).timestamp()
            )
            until_timestamp = int(
                datetime.combine(
                    date_range.end_date, datetime.max.time()
                ).timestamp()
            )

            # Fields needed for VideoInsight and filtering
            video_fields = [
                Video.Field.id,
                Video.Field.title,
                Video.Field.description,
                Video.Field.created_time,
                # Potentially add 'content_category' or check if a specific reel field exists
                # Video.Field.is_instagram_eligible # Example - check available fields
            ]
            video_params = {
                "since": since_timestamp,
                "until": until_timestamp,
                "limit": 100,
            }

            logger.debug(
                f"Fetching videos for page {page_id} between {date_range.start_date} and {date_range.end_date}"
            )
            videos_cursor = await asyncio.to_thread(
                page.get_videos, fields=video_fields, params=video_params
            )
            all_videos = await asyncio.to_thread(list, videos_cursor)
            logger.info(
                f"Found {len(all_videos)} videos for page {page_id} in the specified date range. Filtering for reels if necessary."
            )

            # Filter for reels if possible (FB API might not have a direct filter)
            # This is a placeholder - exact filtering mechanism might depend on available fields
            # reel_videos = [v for v in all_videos if v.get('is_reel', False)] # Fictional field
            reel_videos = all_videos  # Assuming all fetched videos might be reels or we don't filter further
            logger.info(f"Processing {len(reel_videos)} potential reels.")

            # 4. Fetch Insights for Each Reel/Video
            video_details_map = {
                video[Video.Field.id]: video for video in reel_videos
            }

            async def fetch_single_video_insights(video_id):
                try:
                    video = Video(video_id, api=api)
                    insight_params = {
                        "metric": ",".join(metrics),
                        "period": "lifetime",  # Lifetime is common for video insights
                    }
                    insights_result = await asyncio.to_thread(
                        video.get_insights, params=insight_params
                    )

                    if insights_result:
                        insight_data = insights_result[0].export_data()
                        metrics_dict = {}
                        if "values" in insight_data:
                            for value_entry in insight_data["values"]:
                                # Video insights might use 'name' instead of 'verb'
                                metric_name = value_entry.get("name")
                                if metric_name in metrics:
                                    metrics_dict[metric_name] = value_entry.get(
                                        "value", 0
                                    )
                        # Check if metrics are direct keys
                        for metric_name in metrics:
                            if (
                                metric_name in insight_data
                                and metric_name not in metrics_dict
                            ):
                                metrics_dict[metric_name] = insight_data[
                                    metric_name
                                ]

                        video_detail = video_details_map.get(video_id)
                        if video_detail:
                            return VideoInsight(
                                video_id=video_detail[Video.Field.id],
                                title=video_detail.get(Video.Field.title),
                                description=video_detail.get(
                                    Video.Field.description
                                ),
                                created_time=video_detail[
                                    Video.Field.created_time
                                ],
                                metrics=metrics_dict,
                            )
                except FacebookRequestError as e:
                    logger.warning(
                        f"FB API error fetching insights for video {video_id}: {e.message or e}"
                    )
                    self.error_handler.handle_facebook_error(
                        e,
                        f"fetching insights for video {video_id}",
                        raise_exception=False,
                    )
                except Exception as e:
                    logger.error(
                        f"Unexpected error fetching insights for video {video_id}: {e}",
                        exc_info=True,
                    )
                return None

            tasks = [
                fetch_single_video_insights(video_id)
                for video_id in video_details_map.keys()
            ]
            results = await asyncio.gather(*tasks)

            reel_insights_data = [res for res in results if res is not None]
            logger.info(
                f"Successfully fetched insights for {len(reel_insights_data)} reels/videos."
            )

            # 5. Caching
            await self.cache_service.set(
                cache_key,
                [item.dict() for item in reel_insights_data],
                ttl=DEFAULT_CACHE_TTL,
            )
            logger.info(
                f"Cached {len(reel_insights_data)} reel insights for key: {cache_key}"
            )

        except FacebookRequestError as e:
            logger.error(
                f"Facebook API error fetching videos or insights for page {page_id}: {e}",
                exc_info=True,
            )
            self.error_handler.handle_facebook_error(
                e, f"fetching videos/insights for page {page_id}"
            )
            return []
        except Exception as e:
            logger.error(
                f"Unexpected error fetching reel insights for page {page_id}: {e}",
                exc_info=True,
            )
            return []

        return reel_insights_data

    async def get_business_post_insights(
        self,
        business_id: str,
        metrics: List[str],
        date_range: DateRange,
        access_token: Optional[str] = None,
    ) -> List[PostInsight]:
        """
        Fetches post insights for all pages of a Facebook Business.

        Args:
            business_id: The ID of the Facebook Business Manager.
            metrics: List of metrics to retrieve.
            date_range: The start and end date.
            access_token: Token with business_management, pages_read_engagement (nếu không cung cấp, sẽ sử dụng default_token).

        Returns:
            A list of PostInsight objects.

        Raises:
            ApplicationError: If getting insights fails.
        """
        logger.info(
            f"Fetching post insights for Business ID: {business_id}, Metrics: {metrics}"
        )

        # Sử dụng default_token nếu access_token không được cung cấp
        token = access_token or self.default_token
        if not token:
            raise ValueError(
                "No access token provided and no default token set"
            )

        try:
            # 1. Initialize API with the token
            api = await self._get_api_instance(token)

            # 2. Fetch Business Pages using helper
            page_ids = await self._get_business_page_ids(business_id, api)
            if not page_ids:
                return []  # Return early if no pages found/accessible

            # 3. Fetch Insights Concurrently (Posts & Reels)
            logger.info(
                f"Creating tasks for {len(page_ids)} pages (posts and reels)."
            )
            tasks = []
            task_type_map = (
                {}
            )  # To track which task index corresponds to post/reel
            current_task_index = 0

            for page_id in page_ids:
                # Create post insight task
                if metrics:
                    post_task = asyncio.create_task(
                        self.get_post_insights(
                            page_id=page_id,
                            metrics=metrics,
                            date_range=date_range,
                            access_token=token,
                        )
                    )
                    tasks.append(post_task)
                    task_type_map[current_task_index] = ("post", page_id)
                    current_task_index += 1

                # Create reel insight task
                if metrics:
                    reel_task = asyncio.create_task(
                        self.get_reel_insights(
                            page_id=page_id,
                            metrics=metrics,
                            date_range=date_range,
                            access_token=token,
                        )
                    )
                    tasks.append(reel_task)
                    task_type_map[current_task_index] = ("reel", page_id)
                    current_task_index += 1

            logger.info(f"Running {len(tasks)} insight tasks concurrently.")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 4. Aggregate Results Separately
            all_post_insights = []
            all_reel_insights = []
            for i, result in enumerate(results):
                task_info = task_type_map.get(i)
                if not task_info:
                    logger.warning(
                        f"Could not find task info for result index {i}"
                    )
                    continue

                task_type, page_id = task_info

                if isinstance(result, Exception):
                    logger.error(
                        f"Error fetching {task_type} insights for page {page_id}: {result}"
                    )
                elif isinstance(result, list):
                    if task_type == "post":
                        all_post_insights.extend(result)
                    elif task_type == "reel":
                        all_reel_insights.extend(result)
                else:
                    logger.warning(
                        f"Unexpected result type for {task_type} task (page {page_id}): {type(result)}"
                    )

            # Placeholder removed

        except FacebookRequestError as e:
            logger.exception(
                f"Facebook API error fetching business post insights for {business_id}: {e.api_error_message()}"
            )
            raise self.error_handler.handle_error(
                e, f"Failed to fetch business post insights for {business_id}"
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error fetching business post insights for {business_id}: {e}"
            )
            raise self.error_handler.handle_error(
                e, f"Failed fetching business post insights for {business_id}"
            )

        logger.info(
            f"Successfully fetched {len(all_post_insights)} post insights for Business ID: {business_id}"
        )
        return all_post_insights

    async def get_all_business_posts_and_reels_insights(
        self,
        business_id: str,
        post_metrics: List[str],
        reel_metrics: List[str],
        date_range: DateRange,
        access_token: Optional[str] = None,
    ) -> Tuple[List[PostInsight], List[VideoInsight]]:
        """
        Fetches both post and reel insights for all pages of a Facebook Business.

        Retrieves pages, then concurrently fetches post insights and reel insights
        for each page using existing service methods.

        Args:
            business_id: The ID of the Facebook Business Manager.
            post_metrics: Metrics list for regular posts.
            reel_metrics: Metrics list for reels.
            date_range: The start and end date.
            access_token: Token with business_management, pages_read_engagement (nếu không cung cấp, sẽ sử dụng default_token).

        Returns:
            A tuple containing two lists: (all_post_insights, all_reel_insights).

        Raises:
            ApplicationError: If fetching pages or insights fails significantly.
        """
        logger.info(
            f"Fetching all posts and reels insights for Business ID: {business_id}"
        )
        all_post_insights: List[PostInsight] = []
        all_reel_insights: List[VideoInsight] = []

        # Sử dụng default_token nếu access_token không được cung cấp
        token = access_token or self.default_token
        if not token:
            raise ValueError(
                "No access token provided and no default token set"
            )

        try:
            # 1. Initialize API
            api = await self._get_api_instance(token)

            # 2. Fetch Business Pages using helper
            page_ids = await self._get_business_page_ids(business_id, api)
            if not page_ids:
                return [], []  # Return early if no pages found/accessible

            # 3. Fetch Insights Concurrently (Posts & Reels)
            logger.info(
                f"Creating tasks for {len(page_ids)} pages (posts and reels)."
            )
            tasks = []
            task_type_map = (
                {}
            )  # To track which task index corresponds to post/reel
            current_task_index = 0

            for page_id in page_ids:
                # Create post insight task
                if post_metrics:
                    post_task = asyncio.create_task(
                        self.get_post_insights(
                            page_id=page_id,
                            metrics=post_metrics,
                            date_range=date_range,
                            access_token=token,
                        )
                    )
                    tasks.append(post_task)
                    task_type_map[current_task_index] = ("post", page_id)
                    current_task_index += 1

                # Create reel insight task
                if reel_metrics:
                    reel_task = asyncio.create_task(
                        self.get_reel_insights(
                            page_id=page_id,
                            metrics=reel_metrics,
                            date_range=date_range,
                            access_token=token,
                        )
                    )
                    tasks.append(reel_task)
                    task_type_map[current_task_index] = ("reel", page_id)
                    current_task_index += 1

            logger.info(f"Running {len(tasks)} insight tasks concurrently.")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 4. Aggregate Results Separately
            all_post_insights = []
            all_reel_insights = []
            for i, result in enumerate(results):
                task_info = task_type_map.get(i)
                if not task_info:
                    logger.warning(
                        f"Could not find task info for result index {i}"
                    )
                    continue

                task_type, page_id = task_info

                if isinstance(result, Exception):
                    logger.error(
                        f"Error fetching {task_type} insights for page {page_id}: {result}"
                    )
                elif isinstance(result, list):
                    if task_type == "post":
                        all_post_insights.extend(result)
                    elif task_type == "reel":
                        all_reel_insights.extend(result)
                else:
                    logger.warning(
                        f"Unexpected result type for {task_type} task (page {page_id}): {type(result)}"
                    )

            # Placeholder removed

        except FacebookRequestError as e:
            logger.exception(
                f"Facebook API error fetching combined insights for {business_id}: {e.api_error_message()}"
            )
            raise self.error_handler.handle_error(
                e, f"Failed fetching combined insights for {business_id}"
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error fetching combined insights for {business_id}: {e}"
            )
            raise self.error_handler.handle_error(
                e, f"Failed fetching combined insights for {business_id}"
            )

        logger.info(
            f"Successfully fetched {len(all_post_insights)} post insights and "
            f"{len(all_reel_insights)} reel insights for Business ID: {business_id}"
        )
        return all_post_insights, all_reel_insights

    async def check_business_pages_access(
        self,
        business_id: str,
        access_token: str,
    ) -> bool:
        # Implementation of check_business_pages_access method
        pass

    # --- Helper method to fetch business pages ---
    async def _get_business_page_ids(
        self, business_id: str, api: FacebookAdsApi
    ) -> List[str]:
        """Fetches and caches the list of page IDs for a given business ID."""
        page_cache_key_params = {"business_id": business_id}
        page_cache_key = generate_cache_key(
            "fb_business_pages", page_cache_key_params
        )
        cached_pages = await self.cache_service.get(page_cache_key)
        page_ids: List[str] = []

        if cached_pages:
            logger.info(
                f"Using cached page list for Business ID: {business_id}"
            )
            if isinstance(cached_pages, list):
                return cached_pages
            else:
                logger.warning(
                    f"Invalid cache format for {page_cache_key}. Refetching."
                )
                # Fall through to refetch

        logger.info(f"Fetching page list for Business ID: {business_id}")
        try:
            business = Business(business_id, api=api)
            owned_pages_cursor = await asyncio.to_thread(
                business.get_owned_pages, fields=[Page.Field.id]
            )
            for page in owned_pages_cursor:
                page_ids.append(page[Page.Field.id])

            # Consider adding client pages if needed and permissions allow

            page_ids = list(set(page_ids))
            logger.info(
                f"Found {len(page_ids)} pages for Business ID: {business_id}"
            )

            if page_ids:
                await self.cache_service.set(
                    page_cache_key, page_ids, ttl=1800
                )  # 30 min cache
            else:
                logger.warning(f"No pages found for Business ID: {business_id}")

        except FacebookRequestError as e:
            logger.error(
                f"Failed to fetch pages for business {business_id}: {e.api_error_message()}"
            )
            # Propagate the error to be handled by the calling method
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching pages for business {business_id}: {e}"
            )
            raise  # Propagate

        return page_ids

    # --- End helper method ---


# Example usage (for testing or demonstration)
async def main():
    import asyncio

    # Assume CacheService is implemented and initialized
    cache = CacheService(storage_path="./cache")
    service = FacebookAdsService(cache_service=cache)
    # Example requires valid settings and a real access token
    # try:
    #     # Example for campaign insights (replace with actual request and token)
    #     # insights = await service.get_campaign_insights(req, token)
    #     # print(insights)
    #     pass
    # except Exception as e:
    #     print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
