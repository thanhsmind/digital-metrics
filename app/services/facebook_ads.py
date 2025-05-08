import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.adobjects.advideo import AdVideo
from facebook_business.adobjects.business import Business
from facebook_business.adobjects.page import Page
from facebook_business.adobjects.pagepost import PagePost
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


# Removed the temporary Video class definition


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
        # Decrypt token if necessary (not implemented yet)
        decrypted_token = access_token  # Placeholder if not encrypted

        # Create a clean initialization with only the documented parameters
        # This ensures no unexpected parameters are passed to the SDK
        api = FacebookAdsApi.init(
            app_id=settings.FACEBOOK_APP_ID,
            app_secret=settings.FACEBOOK_APP_SECRET,
            access_token=decrypted_token,
            api_version=settings.FACEBOOK_API_VERSION,
        )

        logger.debug(
            f"Facebook API initialized with version {settings.FACEBOOK_API_VERSION}"
        )
        return api

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
            # Use the correct get_insights method from the SDK
            insights_cursor = account.get_insights(
                fields=fields_to_request, params=params, is_async=True
            )
            # Wait for the async job to complete
            async_job = await insights_cursor.execute()
            # Monitor job status
            while True:
                job_status = await asyncio.to_thread(async_job.remote_read)
                if job_status[async_job.Field.async_status] == "Job Completed":
                    break
                elif job_status[async_job.Field.async_status] == "Job Failed":
                    error_message = (
                        job_status.get(async_job.Field.async_response, {})
                        .get("error", {})
                        .get("message", "Unknown async job failure")
                    )
                    raise FacebookRequestError(
                        message=f"Async insights job failed: {error_message}"
                    )
                await asyncio.sleep(5)  # Wait before checking again

            # Fetch results from the completed job
            all_insights = await asyncio.to_thread(async_job.get_result)

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
            self.error_handler.handle_error(  # Renamed method
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

            # 3. Attempt to get Page access token if needed
            try:
                # First try directly with the provided token
                page = Page(page_id, api=api)

                # Fetch Posts within Date Range
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

                # Specify fields including status_type
                post_fields = [
                    PagePost.Field.id,
                    PagePost.Field.created_time,
                    PagePost.Field.message,
                    PagePost.Field.status_type,
                ]
                post_params = {
                    "since": since_timestamp,
                    "until": until_timestamp,
                    "limit": 100,
                }

                logger.debug(
                    f"Fetching posts for page {page_id} between {date_range.start_date} and {date_range.end_date}"
                )

                # Try to get posts, which might fail if we need a Page token
                try:
                    posts_cursor = await asyncio.to_thread(
                        page.get_posts, fields=post_fields, params=post_params
                    )
                    all_posts = await asyncio.to_thread(list, posts_cursor)
                except FacebookRequestError as e:
                    # Check if the error is related to token type
                    if (
                        e.api_error_code() == 190
                        and e.api_error_subcode() == 2069032
                    ):
                        logger.info(
                            f"User access token not supported for page {page_id}, attempting to get page access token"
                        )

                        # Try to get page token using the user token
                        try:
                            page_info = await asyncio.to_thread(
                                Page(page_id, api=api).api_get,
                                fields=["access_token"],
                            )

                            # If we got a page access token, reinitialize the API
                            if "access_token" in page_info:
                                page_token = page_info["access_token"]
                                logger.info(
                                    f"Successfully obtained page access token for page {page_id}"
                                )

                                # Reinitialize API with page token
                                api = await self._get_api_instance(page_token)
                                page = Page(page_id, api=api)

                                # Retry the posts request with the page token
                                posts_cursor = await asyncio.to_thread(
                                    page.get_posts,
                                    fields=post_fields,
                                    params=post_params,
                                )
                                all_posts = await asyncio.to_thread(
                                    list, posts_cursor
                                )
                            else:
                                logger.error(
                                    f"Could not obtain page access token for page {page_id}"
                                )
                                return []
                        except FacebookRequestError as token_error:
                            logger.error(
                                f"Failed to get page access token for page {page_id}: {token_error}"
                            )
                            return []
                    else:
                        # Not a token type error, re-raise
                        raise

                logger.info(
                    f"Found {len(all_posts)} posts for page {page_id} in the specified date range."
                )

                # 4. Fetch Insights for Each Post
                post_details_map = {
                    post[PagePost.Field.id]: post for post in all_posts
                }

                async def fetch_single_post_insights(post_id):
                    try:
                        post = PagePost(post_id, api=api)
                        # Construct insight params - period 'lifetime' often used for post insights
                        insight_params = {
                            # Metrics go in 'fields' for get_insights
                            "period": "lifetime",
                        }
                        # Use fields=metrics and params=insight_params
                        insights_result = await asyncio.to_thread(
                            post.get_insights,
                            fields=metrics,
                            params=insight_params,
                        )

                        if insights_result:
                            # Insights for a post usually return a list with one item
                            insight_data = insights_result[0].export_data()
                            metrics_dict = {}
                            # Insights data structure can vary, check 'values' first
                            if "values" in insight_data and isinstance(
                                insight_data["values"], list
                            ):
                                for value_entry in insight_data["values"]:
                                    metric_name = value_entry.get(
                                        "name"
                                    )  # Video insights use 'name'
                                    if metric_name in metrics:
                                        metrics_dict[metric_name] = (
                                            value_entry.get("value", 0)
                                        )
                                    # Handle post metrics which might use 'verb'
                                    verb_name = value_entry.get("verb")
                                    if verb_name in metrics:
                                        metrics_dict[verb_name] = (
                                            value_entry.get("value", 0)
                                        )

                            # Fallback: Check if metrics are direct keys in insight_data
                            for metric_name in metrics:
                                if (
                                    metric_name in insight_data
                                    and metric_name not in metrics_dict
                                ):
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
                                    message=post_detail.get(
                                        PagePost.Field.message
                                    ),
                                    type=post_detail.get(
                                        PagePost.Field.status_type
                                    ),  # Assign status_type to type field
                                    metrics=metrics_dict,
                                )
                    except FacebookRequestError as e:
                        # Log error for specific post but continue with others
                        logger.warning(
                            f"FB API error fetching insights for post {post_id}: {e.api_error_message()}"
                        )
                        # Use correct handler method name
                        self.error_handler.handle_error(
                            e,
                            f"fetching insights for post {post_id}",
                            # raise_exception=False, # handle_error doesn't take this
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
                # Use correct handler method name
                self.error_handler.handle_error(
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

            # 3. Attempt to get Page access token if needed
            try:
                # First try with the provided token
                page = Page(page_id, api=api)

                # Set up the timestamp range
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
                    AdVideo.Field.id,
                    AdVideo.Field.title,
                    AdVideo.Field.description,
                    AdVideo.Field.created_time,
                ]
                video_params = {
                    "since": since_timestamp,
                    "until": until_timestamp,
                    "limit": 100,
                    "type": "uploaded",
                }

                logger.debug(
                    f"Fetching videos for page {page_id} between {date_range.start_date} and {date_range.end_date}"
                )

                # Try to get videos, which might fail if we need a Page token
                try:
                    # Use page.get_videos which is designed for this purpose
                    videos_cursor = await asyncio.to_thread(
                        page.get_videos,
                        fields=video_fields,
                        params=video_params,
                    )
                    all_videos = await asyncio.to_thread(list, videos_cursor)
                except FacebookRequestError as e:
                    # Check if the error is related to token type
                    if (
                        e.api_error_code() == 190
                        and e.api_error_subcode() == 2069032
                    ):
                        logger.info(
                            f"User access token not supported for page {page_id}, attempting to get page access token"
                        )

                        # Try to get page token using the user token
                        try:
                            page_info = await asyncio.to_thread(
                                Page(page_id, api=api).api_get,
                                fields=["access_token"],
                            )

                            # If we got a page access token, reinitialize the API
                            if "access_token" in page_info:
                                page_token = page_info["access_token"]
                                logger.info(
                                    f"Successfully obtained page access token for page {page_id}"
                                )

                                # Reinitialize API with page token
                                api = await self._get_api_instance(page_token)
                                page = Page(page_id, api=api)

                                # Retry the videos request with the page token
                                videos_cursor = await asyncio.to_thread(
                                    page.get_videos,
                                    fields=video_fields,
                                    params=video_params,
                                )
                                all_videos = await asyncio.to_thread(
                                    list, videos_cursor
                                )
                            else:
                                logger.error(
                                    f"Could not obtain page access token for page {page_id}"
                                )
                                return []
                        except FacebookRequestError as token_error:
                            logger.error(
                                f"Failed to get page access token for page {page_id}: {token_error}"
                            )
                            return []
                    else:
                        # Not a token type error, re-raise
                        raise

                logger.info(
                    f"Found {len(all_videos)} videos/reels for page {page_id} in the specified date range."
                )

                # Filter for reels if possible
                reel_videos = all_videos
                logger.info(f"Processing {len(reel_videos)} potential reels.")

                # 4. Fetch Insights for Each Reel/Video
                video_details_map = {
                    video[AdVideo.Field.id]: video for video in reel_videos
                }

                async def fetch_single_video_insights(video_id):
                    try:
                        # Ensure the URL has a proper scheme
                        if not video_id.startswith(("http://", "https://")):
                            # Just use the ID directly instead of as a URL
                            video = AdVideo(video_id, api=api)
                        else:
                            video = AdVideo(video_id, api=api)

                        # Video insights expect metrics via the 'fields' argument
                        insight_params = {
                            "period": "lifetime",  # Lifetime is common for video insights
                        }

                        # Use the SDK's get_insights method directly
                        insights_result = await asyncio.to_thread(
                            video.get_insights,
                            fields=metrics,
                            params=insight_params,
                        )

                        if insights_result:
                            # Process insights
                            processed_insights = []
                            for insight in insights_result:
                                insight_data = insight.export_data()
                                metrics_dict = {}
                                # Check 'values' structure first (often used for posts)
                                if "values" in insight_data and isinstance(
                                    insight_data["values"], list
                                ):
                                    for value_entry in insight_data["values"]:
                                        metric_name = value_entry.get(
                                            "name"
                                        )  # Video insights tend to use 'name'
                                        if metric_name in metrics:
                                            metrics_dict[metric_name] = (
                                                value_entry.get("value", 0)
                                            )
                                # Fallback: Check if metrics are direct keys
                                else:
                                    for metric_name in metrics:
                                        if metric_name in insight_data:
                                            metrics_dict[metric_name] = (
                                                insight_data[metric_name]
                                            )

                                # If we got any metrics, add to list for this video
                                if metrics_dict:
                                    processed_insights.append(metrics_dict)

                            # Aggregate metrics if multiple insights returned per video
                            final_metrics_dict = (
                                processed_insights[0]
                                if processed_insights
                                else {}
                            )

                            video_detail = video_details_map.get(video_id)
                            if video_detail:
                                return VideoInsight(
                                    video_id=video_detail[AdVideo.Field.id],
                                    title=video_detail.get(AdVideo.Field.title),
                                    description=video_detail.get(
                                        AdVideo.Field.description
                                    ),
                                    created_time=video_detail[
                                        AdVideo.Field.created_time
                                    ],
                                    metrics=final_metrics_dict,
                                )
                    except FacebookRequestError as e:
                        logger.warning(
                            f"FB API error fetching insights for video {video_id}: {e.api_error_message()}"
                        )
                        self.error_handler.handle_error(
                            e,
                            f"fetching insights for video {video_id}",
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
                # Use correct handler method name
                self.error_handler.handle_error(
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

        all_post_insights: List[PostInsight] = []
        try:
            # 1. Initialize API with the token
            api = await self._get_api_instance(token)

            # 2. Fetch Business Pages using helper
            page_ids = await self._get_business_page_ids(business_id, api)
            if not page_ids:
                return []  # Return early if no pages found/accessible

            # 3. Fetch Insights Concurrently for Posts Only
            logger.info(f"Creating tasks for {len(page_ids)} pages (posts).")
            tasks = []
            for page_id in page_ids:
                if metrics:  # Only schedule if metrics are requested
                    task = asyncio.create_task(
                        self.get_post_insights(
                            page_id=page_id,
                            metrics=metrics,
                            date_range=date_range,
                            access_token=token,  # Pass the token for each page call
                        )
                    )
                    tasks.append(task)

            if not tasks:
                logger.info("No post insight tasks to run.")
                return []

            logger.info(
                f"Running {len(tasks)} post insight tasks concurrently."
            )
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 4. Aggregate Results
            for i, result in enumerate(results):
                page_id = page_ids[i]  # Assuming order is maintained
                if isinstance(result, Exception):
                    logger.error(
                        f"Error fetching post insights for page {page_id}: {result}"
                    )
                    # Optionally, collect errors or re-raise depending on desired behavior
                elif isinstance(result, list):
                    all_post_insights.extend(result)
                else:
                    logger.warning(
                        f"Unexpected result type for post task (page {page_id}): {type(result)}"
                    )

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
                logger.warning(
                    f"No accessible pages found for Business ID: {business_id}"
                )
                return [], []  # Return early if no pages found/accessible

            # 3. Fetch Insights Concurrently (Posts & Reels)
            logger.info(
                f"Creating tasks for {len(page_ids)} pages (posts and reels)."
            )
            tasks = []
            task_info_map = {}  # Maps task index to (type, page_id)

            current_task_index = 0
            for page_id in page_ids:
                # Create post insight task if post_metrics are requested
                if post_metrics:
                    post_task = asyncio.create_task(
                        self.get_post_insights(
                            page_id=page_id,
                            metrics=post_metrics,
                            date_range=date_range,
                            access_token=token,  # Pass token for each page call
                        )
                    )
                    tasks.append(post_task)
                    task_info_map[current_task_index] = ("post", page_id)
                    current_task_index += 1

                # Create reel insight task if reel_metrics are requested
                if reel_metrics:
                    reel_task = asyncio.create_task(
                        self.get_reel_insights(
                            page_id=page_id,
                            metrics=reel_metrics,
                            date_range=date_range,
                            access_token=token,  # Pass token for each page call
                        )
                    )
                    tasks.append(reel_task)
                    task_info_map[current_task_index] = ("reel", page_id)
                    current_task_index += 1

            if not tasks:
                logger.warning(
                    "No post or reel metrics requested, returning empty results."
                )
                return [], []

            logger.info(f"Running {len(tasks)} insight tasks concurrently.")
            # Use return_exceptions=True to handle individual task failures
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 4. Aggregate Results Separately
            all_post_insights = []
            all_reel_insights = []
            for i, result in enumerate(results):
                task_info = task_info_map.get(i)
                if not task_info:
                    logger.warning(
                        f"Could not find task info for result index {i}"
                    )
                    continue

                task_type, page_id = task_info

                if isinstance(result, Exception):
                    # Log the specific error for the page/task
                    logger.error(
                        f"Error fetching {task_type} insights for page {page_id}: {result}",
                        exc_info=isinstance(
                            result, FacebookRequestError
                        ),  # Log traceback for FB errors
                    )
                    # Optionally re-raise if one failure should stop everything,
                    # or collect errors to return/handle later.
                    # For now, we just log and continue to gather results from other pages.
                elif isinstance(result, list):
                    if task_type == "post":
                        all_post_insights.extend(result)
                    elif task_type == "reel":
                        all_reel_insights.extend(result)
                else:
                    logger.warning(
                        f"Unexpected result type for {task_type} task (page {page_id}): {type(result)}"
                    )

        except FacebookRequestError as e:
            # This handles errors during initial API setup or fetching page IDs
            logger.exception(
                f"Facebook API error during setup/page fetch for {business_id}: {e.api_error_message()}"
            )
            # Use correct handler method name
            self.error_handler.handle_error(
                e, f"Failed fetching pages/initial setup for {business_id}"
            )
            # Re-raise or return depending on desired handling
            raise  # Re-raise the handled HTTPException
        except Exception as e:
            # This catches other unexpected errors during setup/page fetch
            logger.exception(
                f"Unexpected error fetching combined insights for {business_id}: {e}"
            )
            # Use correct handler method name
            self.error_handler.handle_error(
                e, f"Failed fetching combined insights for {business_id}"
            )
            raise  # Re-raise the handled HTTPException

        logger.info(
            f"Successfully gathered results for {len(all_post_insights)} post insights and "
            f"{len(all_reel_insights)} reel insights for Business ID: {business_id}"
        )
        return all_post_insights, all_reel_insights

    async def check_business_pages_access(
        self,
        business_id: str,
        access_token: str,
    ) -> bool:
        """
        Checks if the provided token has access to the pages of a given business.
        (Basic implementation - might need refinement based on exact needs)
        """
        logger.info(f"Checking page access for Business ID: {business_id}")
        try:
            api = await self._get_api_instance(access_token)
            # Attempt to fetch page IDs as a way to check access
            await self._get_business_page_ids(business_id, api)
            logger.info(
                f"Token has access to pages for Business ID: {business_id}"
            )
            return True
        except FacebookRequestError as e:
            # Handle specific permission or access errors if needed
            logger.warning(
                f"Token access check failed for Business ID {business_id}: {e.api_error_message()}"
            )
            self.error_handler.handle_error(
                e, f"Checking page access for {business_id}"
            )
            return False  # Or re-raise depending on desired behavior
        except Exception as e:
            logger.error(
                f"Unexpected error during page access check for {business_id}: {e}",
                exc_info=True,
            )
            return False

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
            # Fetch owned pages
            owned_pages_cursor = await asyncio.to_thread(
                business.get_owned_pages, fields=[Page.Field.id]
            )
            for page in owned_pages_cursor:
                page_ids.append(page[Page.Field.id])

            # Fetch client pages (requires appropriate permissions)
            try:
                client_pages_cursor = await asyncio.to_thread(
                    business.get_client_pages, fields=[Page.Field.id]
                )
                for page in client_pages_cursor:
                    page_ids.append(page[Page.Field.id])
            except FacebookRequestError as client_page_error:
                # Log if fetching client pages fails (e.g., due to permissions), but don't fail the whole process
                logger.warning(
                    f"Could not fetch client pages for business {business_id}: {client_page_error.api_error_message()}"
                )

            page_ids = list(set(page_ids))  # Remove duplicates
            logger.info(
                f"Found {len(page_ids)} pages (owned + client) for Business ID: {business_id}"
            )

            if page_ids:
                await self.cache_service.set(
                    page_cache_key, page_ids, ttl=1800
                )  # 30 min cache
            else:
                logger.warning(
                    f"No pages found or accessible for Business ID: {business_id}"
                )

        except FacebookRequestError as e:
            # Log more specific error if possible
            logger.error(
                f"Failed to fetch pages for business {business_id}: {e.api_error_code()} - {e.api_error_message()}",
                exc_info=True,
            )
            # Propagate the error to be handled by the calling method
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching pages for business {business_id}: {e}",
                exc_info=True,
            )
            raise  # Propagate

        return page_ids

    # --- End helper method ---

    async def get_business_reel_insights(
        self,
        business_id: str,
        metrics: List[str],
        date_range: DateRange,
        access_token: Optional[str] = None,
    ) -> List[VideoInsight]:
        """
        Fetch reel/video insights for all Pages associated with a Business Manager.

        Args:
            business_id: The Facebook Business Manager ID
            metrics: List of metrics to retrieve for each reel
            date_range: Date range for fetching reels (based on creation time)
            access_token: Optional Facebook access token with business_management permission

        Returns:
            List of VideoInsight objects with insights for all reels across all pages
        """
        # Use provided token or default token if available
        token = access_token or self.default_token
        if not token:
            logger.error("No access token provided for business reel insights")
            return []

        try:
            # 1. Initialize API with the token
            api = await self._get_api_instance(token)

            # 2. Fetch Business Pages using helper
            page_ids = await self._get_business_page_ids(business_id, api)
            if not page_ids:
                return []  # Return early if no pages found/accessible

            # 3. Fetch Insights Concurrently for Reels Only
            logger.info(f"Creating tasks for {len(page_ids)} pages (reels).")
            tasks = []
            for page_id in page_ids:
                if metrics:  # Only schedule if metrics are requested
                    task = asyncio.create_task(
                        self.get_reel_insights(
                            page_id=page_id,
                            metrics=metrics,
                            date_range=date_range,
                            access_token=token,  # Pass the token for each page call
                        )
                    )
                    tasks.append(task)

            if not tasks:
                logger.info("No reel insight tasks to run.")
                return []

            logger.info(
                f"Running {len(tasks)} reel insight tasks concurrently."
            )
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 4. Process Results
            all_insights = []
            for i, result in enumerate(results):
                page_id = page_ids[i]
                if isinstance(result, Exception):
                    logger.error(
                        f"Error fetching reel insights for page {page_id}: {result}"
                    )
                else:
                    # Add the insights for this page to the combined results
                    all_insights.extend(result)

            logger.info(
                f"Retrieved {len(all_insights)} reel insights across {len(page_ids)} pages."
            )
            return all_insights

        except Exception as e:
            logger.error(
                f"Unexpected error fetching business reel insights for {business_id}: {str(e)}"
            )
            raise


# Example usage (for testing or demonstration)
async def main():
    import asyncio

    from app.utils.cache_factory import get_cache  # Assuming you have a factory

    # Assume CacheService is implemented and initialized
    # cache = CacheService(storage_path="./cache") # Or use your factory
    cache = get_cache()
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
    # Setup basic logging for testing
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
