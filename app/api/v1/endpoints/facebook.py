import csv
import logging
from datetime import date, datetime
from io import StringIO
from typing import Any, Dict, List, Optional

from facebook_business.exceptions import FacebookRequestError
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.constants import (
    AVAILABLE_ADS_METRICS,
    AVAILABLE_METRICS,
    AVAILABLE_METRICS_DICT,
    AVAILABLE_REEL_METRICS,
    DEFAULT_POST_METRICS,
    DEFAULT_REEL_METRICS,
)
from app.core.dependencies import (
    get_cache_service,
    get_facebook_service,
    get_placeholder_token,
    oauth2_scheme,
)
from app.models import (
    DateRange,
    FacebookCampaignMetricsRequest,
    FacebookMetricsResponse,
    PostInsight,
)
from app.services.cache_service import CacheService
from app.services.facebook.token_manager import TokenManager
from app.services.facebook_ads import FacebookAdsService
from app.utils.csv_utils import generate_csv_response
from app.utils.validation import validate_date_range

router = APIRouter()
token_manager = TokenManager()


@router.get(
    "/business_post_insights_csv",
    response_class=StreamingResponse,
    summary="Get Business Post Insights as CSV",
    description="Retrieves post insights for all pages associated with a Facebook Business and returns the data as a CSV file.",
    tags=["Facebook Business Insights", "CSV Export"],
)
async def get_business_post_insights_csv(
    business_id: str = Query(
        ..., description="ID of the Facebook Business Manager."
    ),
    metrics: Optional[str] = Query(
        default=",".join(DEFAULT_POST_METRICS),
        description=f"Comma-separated list of post metrics. Defaults to '{','.join(DEFAULT_POST_METRICS)}'. Available: {', '.join(AVAILABLE_METRICS)}",
    ),
    since_date: date = Query(
        ..., description="Start date (YYYY-MM-DD) for post creation time."
    ),
    until_date: date = Query(
        ..., description="End date (YYYY-MM-DD) for post creation time."
    ),
    token: Optional[str] = Query(
        None,
        description="Facebook access token with business_management permission. If not provided, will try to use business token from storage.",
    ),
    service: FacebookAdsService = Depends(get_facebook_service),
):
    """
    Get post insights for all pages of a business in CSV format.

    - **business_id**: The ID of the target Facebook Business Manager.
    - **metrics**: Comma-separated list of metrics to retrieve.
    - **since_date**: Start date for filtering posts.
    - **until_date**: End date for filtering posts.
    - **token**: Optional Facebook access token. If not provided, will try to use business token from storage.
    """
    if until_date < since_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be before start date."
        )

    today = datetime.now().date()
    if since_date > today:
        raise HTTPException(
            status_code=400, detail="Start date cannot be in the future."
        )

    if until_date > today:
        raise HTTPException(
            status_code=400, detail="End date cannot be in the future."
        )

    metrics_list = DEFAULT_POST_METRICS

    if metrics:
        raw_metrics = [m.strip() for m in metrics.split(",") if m.strip()]
        if not raw_metrics:
            metrics_list = DEFAULT_POST_METRICS
        else:
            valid_metrics = [m for m in raw_metrics if m in AVAILABLE_METRICS]
            invalid_metrics = [
                m for m in raw_metrics if m not in AVAILABLE_METRICS
            ]
            if not valid_metrics:
                logging.error("No valid metrics provided")
                raise HTTPException(
                    status_code=400,
                    detail=f"No valid metrics provided. Invalid: {', '.join(invalid_metrics)}. Available: {', '.join(AVAILABLE_METRICS)}",
                )
            if invalid_metrics:
                print(
                    f"Warning: Ignoring invalid metrics: {', '.join(invalid_metrics)}"
                )
            metrics_list = valid_metrics

    date_range_obj = DateRange(start_date=since_date, end_date=until_date)

    try:
        logging.error(
            f"Start get business post insights csv {business_id} - {token}"
        )
        # Nếu không có token được cung cấp, thử lấy từ storage
        if not token:
            token = await token_manager.get_business_token(business_id)
            if not token:
                raise HTTPException(
                    status_code=404,
                    detail=f"No token found for business_id: {business_id}. Please provide a token or use /auth/facebook/business-token endpoint to store one.",
                )

        # Kiểm tra quyền của token
        required_permissions = ["business_management", "pages_read_engagement"]
        permission_check = await token_manager.check_token_permissions(
            token, required_permissions
        )
        print(f"Check permission: {permission_check}")

        if not permission_check.has_permission:
            if permission_check.token_status == "expired":
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": "Token has expired",
                        "authentication_url": permission_check.authorization_url,
                    },
                )
            elif permission_check.token_status == "invalid":
                raise HTTPException(
                    status_code=401,
                    detail={"message": permission_check.message},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Token lacks required permissions: {', '.join(permission_check.missing_permissions)}",
                        "authentication_url": permission_check.authorization_url,
                    },
                )

        # Thực hiện truy vấn với token có quyền
        service.update_access_token(token)
        insights: List[PostInsight] = await service.get_business_post_insights(
            business_id=business_id,
            metrics=metrics_list,
            date_range=date_range_obj,
        )

        filename = f"business_{business_id}_post_insights_{since_date}_to_{until_date}.csv"
        return await generate_csv_response(data=insights, filename=filename)

    except FacebookRequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Facebook API Error: {e.api_error_message()} (Code: {e.api_error_code()}, Subcode: {e.api_error_subcode()})",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(
            f"Error generating business post insights CSV for {business_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while processing request.",
        )


@router.get(
    "/business_posts_and_reels_insights_csv",
    response_class=StreamingResponse,
    summary="Get Business Posts and Reels Insights as CSV",
    description="Retrieves post and reel insights for all pages associated with a Facebook Business and returns the data as a CSV file.",
    tags=["Facebook Business Insights", "CSV Export"],
)
async def get_business_posts_and_reels_insights_csv(
    business_id: str = Query(
        ..., description="ID of the Facebook Business Manager."
    ),
    post_metrics: Optional[str] = Query(
        default=",".join(DEFAULT_POST_METRICS),
        description=f"Comma-separated list of post metrics. Defaults to '{','.join(DEFAULT_POST_METRICS)}'. Available: {', '.join(AVAILABLE_METRICS)}",
    ),
    reel_metrics: Optional[str] = Query(
        default=",".join(DEFAULT_REEL_METRICS),
        description=f"Comma-separated list of reel metrics. Defaults to '{','.join(DEFAULT_REEL_METRICS)}'. Available: {', '.join(AVAILABLE_REEL_METRICS)}",
    ),
    since_date: date = Query(
        ..., description="Start date (YYYY-MM-DD) for post creation time."
    ),
    until_date: date = Query(
        ..., description="End date (YYYY-MM-DD) for post creation time."
    ),
    token: Optional[str] = Query(
        None,
        description="Facebook access token with business_management permission. If not provided, will try to use business token from storage.",
    ),
    service: FacebookAdsService = Depends(get_facebook_service),
):
    """
    Get post and reel insights for all pages of a business in CSV format.

    - **business_id**: The ID of the target Facebook Business Manager.
    - **post_metrics**: Comma-separated list of post metrics to retrieve.
    - **reel_metrics**: Comma-separated list of reel metrics to retrieve.
    - **since_date**: Start date for filtering posts and reels.
    - **until_date**: End date for filtering posts and reels.
    - **token**: Optional Facebook access token. If not provided, will try to use business token from storage.
    """
    if until_date < since_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be before start date."
        )

    today = datetime.now().date()
    if since_date > today:
        raise HTTPException(
            status_code=400, detail="Start date cannot be in the future."
        )

    if until_date > today:
        raise HTTPException(
            status_code=400, detail="End date cannot be in the future."
        )

    # Process and validate post metrics
    post_metrics_list = DEFAULT_POST_METRICS
    if post_metrics:
        raw_metrics = [m.strip() for m in post_metrics.split(",") if m.strip()]
        if not raw_metrics:
            post_metrics_list = DEFAULT_POST_METRICS
        else:
            valid_metrics = [m for m in raw_metrics if m in AVAILABLE_METRICS]
            invalid_metrics = [
                m for m in raw_metrics if m not in AVAILABLE_METRICS
            ]
            if not valid_metrics:
                raise HTTPException(
                    status_code=400,
                    detail=f"No valid post metrics provided. Invalid: {', '.join(invalid_metrics)}. Available: {', '.join(AVAILABLE_METRICS)}",
                )
            if invalid_metrics:
                print(
                    f"Warning: Ignoring invalid post metrics: {', '.join(invalid_metrics)}"
                )
            post_metrics_list = valid_metrics

    # Process and validate reel metrics
    reel_metrics_list = DEFAULT_REEL_METRICS
    if reel_metrics:
        raw_metrics = [m.strip() for m in reel_metrics.split(",") if m.strip()]
        if not raw_metrics:
            reel_metrics_list = DEFAULT_REEL_METRICS
        else:
            valid_metrics = [
                m for m in raw_metrics if m in AVAILABLE_REEL_METRICS
            ]
            invalid_metrics = [
                m for m in raw_metrics if m not in AVAILABLE_REEL_METRICS
            ]
            if not valid_metrics:
                raise HTTPException(
                    status_code=400,
                    detail=f"No valid reel metrics provided. Invalid: {', '.join(invalid_metrics)}. Available: {', '.join(AVAILABLE_REEL_METRICS)}",
                )
            if invalid_metrics:
                print(
                    f"Warning: Ignoring invalid reel metrics: {', '.join(invalid_metrics)}"
                )
            reel_metrics_list = valid_metrics

    date_range_obj = DateRange(start_date=since_date, end_date=until_date)

    try:
        # Nếu không có token được cung cấp, thử lấy từ storage
        if not token:
            token = await token_manager.get_business_token(business_id)
            if not token:
                raise HTTPException(
                    status_code=404,
                    detail=f"No token found for business_id: {business_id}. Please provide a token or use /auth/facebook/business-token endpoint to store one.",
                )

        # Kiểm tra quyền của token
        required_permissions = ["business_management", "pages_read_engagement"]
        permission_check = await token_manager.check_token_permissions(
            token, required_permissions
        )

        if not permission_check.has_permission:
            if permission_check.token_status == "expired":
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": "Token has expired",
                        "authentication_url": permission_check.authorization_url,
                    },
                )
            elif permission_check.token_status == "invalid":
                raise HTTPException(
                    status_code=401,
                    detail={"message": permission_check.message},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Token lacks required permissions: {', '.join(permission_check.missing_permissions)}",
                        "authentication_url": permission_check.authorization_url,
                    },
                )

        # Thực hiện truy vấn với token có quyền
        service.update_access_token(token)
        post_insights = await service.get_business_post_insights(
            business_id=business_id,
            metrics=post_metrics_list,
            date_range=date_range_obj,
        )
        reel_insights = await service.get_business_reel_insights(
            business_id=business_id,
            metrics=reel_metrics_list,
            date_range=date_range_obj,
        )

        # Combine post and reel insights
        combined_insights = post_insights + reel_insights

        filename = f"business_{business_id}_posts_reels_insights_{since_date}_to_{until_date}.csv"
        return await generate_csv_response(
            data=combined_insights, filename=filename
        )

    except FacebookRequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Facebook API Error: {e.api_error_message()} (Code: {e.api_error_code()}, Subcode: {e.api_error_subcode()})",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(
            f"Error generating business posts and reels insights CSV for {business_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while processing request.",
        )


@router.post(
    "/campaign_metrics",
    response_model=FacebookMetricsResponse,
    summary="Get Campaign Metrics",
    description="Retrieve metrics for a specific Facebook advertising campaign.",
    tags=["Facebook Ads"],
)
async def get_campaign_metrics(
    request: FacebookCampaignMetricsRequest,
    token: Optional[str] = None,
    service: FacebookAdsService = Depends(get_facebook_service),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Get metrics for a specific Facebook advertising campaign.

    - **campaign_id**: ID of the campaign to retrieve metrics for.
    - **metrics**: List of metrics to retrieve. If not provided, defaults to standard metrics.
    - **start_date**: Start date for the metrics calculation period.
    - **end_date**: End date for the metrics calculation period.
    - **token**: Optional Facebook access token. If not provided, will try to use business token from storage.
    """
    # Xác định cache key dựa trên request
    cache_key = f"campaign_{request.campaign_id}_{request.start_date}_{request.end_date}_{','.join(request.metrics)}"

    # Kiểm tra dữ liệu từ cache
    cached_data = await cache.get(cache_key)
    if cached_data:
        print(f"Cache hit for {cache_key}")
        return FacebookMetricsResponse(data=cached_data, from_cache=True)

    try:
        # Nếu không có token được cung cấp, thử lấy từ storage
        business_id = await service.get_business_id_from_campaign(
            request.campaign_id
        )
        if not token and business_id:
            token = await token_manager.get_business_token(business_id)
            if not token:
                raise HTTPException(
                    status_code=404,
                    detail=f"No token found for business_id: {business_id}. Please provide a token or use /auth/facebook/business-token endpoint to store one.",
                )
        elif not token:
            raise HTTPException(
                status_code=400,
                detail="Token is required. Either provide it directly or ensure the campaign is linked to a business with a stored token.",
            )

        # Kiểm tra quyền của token
        required_permissions = ["business_management", "ads_read"]
        permission_check = await token_manager.check_token_permissions(
            token, required_permissions
        )

        if not permission_check.has_permission:
            if permission_check.token_status == "expired":
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": "Token has expired",
                        "authentication_url": permission_check.authorization_url,
                    },
                )
            elif permission_check.token_status == "invalid":
                raise HTTPException(
                    status_code=401,
                    detail={"message": permission_check.message},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Token lacks required permissions: {', '.join(permission_check.missing_permissions)}",
                        "authentication_url": permission_check.authorization_url,
                    },
                )

        # Thực hiện truy vấn với token có quyền
        service.update_access_token(token)
        date_range_obj = DateRange(
            start_date=request.start_date, end_date=request.end_date
        )

        campaign_metrics = await service.get_campaign_metrics(
            campaign_id=request.campaign_id,
            metrics=request.metrics,
            date_range=date_range_obj,
        )

        # Lưu kết quả vào cache cho 1 giờ (3600 giây)
        await cache.set(cache_key, campaign_metrics, ttl=3600)

        return FacebookMetricsResponse(data=campaign_metrics, from_cache=False)

    except FacebookRequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Facebook API Error: {e.api_error_message()} (Code: {e.api_error_code()}, Subcode: {e.api_error_subcode()})",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(
            f"Error retrieving campaign metrics for {request.campaign_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while processing request.",
        )


@router.get(
    "/campaign_metrics_csv",
    response_class=StreamingResponse,
    summary="Get Facebook Campaign Insights as CSV",
    description="Retrieves insights metrics for Facebook campaigns and returns the data as a CSV file.",
    tags=["Facebook Metrics", "CSV Export"],
)
async def get_campaign_metrics_csv(
    ad_account_id: str = Query(
        ...,
        description="ID of the Facebook Ad Account (without 'act_' prefix).",
    ),
    campaign_ids: Optional[str] = Query(
        None,
        description="Optional comma-separated list of Campaign IDs to filter by.",
    ),
    metrics: str = Query(
        ",".join(DEFAULT_REEL_METRICS),
        description="Comma-separated list of campaign metrics to retrieve.",
        example="spend,impressions,clicks",
    ),
    dimensions: Optional[str] = Query(
        None,
        description="Optional comma-separated list of dimensions to break down by (e.g., age, gender).",
    ),
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)."),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)."),
    token: Optional[str] = Query(
        None,
        description="Facebook access token with ads_read permission. If not provided, will try to use business token from storage.",
    ),
    service: FacebookAdsService = Depends(get_facebook_service),
    cache: CacheService = Depends(get_cache_service),
):
    """Fetches Facebook campaign insights and returns as CSV."""
    logger.info(
        f"Received request for campaign metrics CSV for account: {ad_account_id}"
    )

    # Parse and Validate Metrics
    requested_metrics = [m.strip() for m in metrics.split(",") if m.strip()]
    invalid_metrics = [
        m for m in requested_metrics if m not in AVAILABLE_REEL_METRICS
    ]
    if invalid_metrics:
        # Return error as plain text for CSV endpoint, or raise HTTPException
        # For now, raise HTTPException for consistency
        logger.warning(
            f"Request rejected due to invalid campaign metrics: {invalid_metrics}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metrics: {invalid_metrics}. Available: {AVAILABLE_REEL_METRICS}",
        )
    if not requested_metrics:
        raise HTTPException(status_code=400, detail="No metrics provided.")

    # Parse Dimensions
    requested_dimensions = (
        [d.strip() for d in dimensions.split(",") if d.strip()]
        if dimensions
        else []
    )

    # Parse Campaign IDs
    requested_campaign_ids = (
        [c.strip() for c in campaign_ids.split(",") if c.strip()]
        if campaign_ids
        else None
    )

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be before start date."
        )

    today = datetime.now().date()
    if start_date > today:
        raise HTTPException(
            status_code=400, detail="Start date cannot be in the future."
        )

    if end_date > today:
        raise HTTPException(
            status_code=400, detail="End date cannot be in the future."
        )

    try:
        # Nếu không có token được cung cấp, thử lấy từ storage
        if not token:
            # Thử lấy business token từ storage dựa trên ad_account_id
            business_id = None
            try:
                # Nếu có service method để lấy business_id từ account_id, sử dụng nó
                if hasattr(service, "get_business_id_from_account"):
                    business_id = await service.get_business_id_from_account(
                        ad_account_id
                    )
            except Exception as e:
                logger.warning(
                    f"Could not determine business ID for account {ad_account_id}: {e}"
                )

            if business_id:
                token = await token_manager.get_business_token(business_id)
                if not token:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No token found for business_id: {business_id}. Please provide a token or use /auth/facebook/business-token endpoint to store one.",
                    )
            else:
                # Thử lấy token chung nếu không có business token
                token = await token_manager.load_token()
                if not token:
                    raise HTTPException(
                        status_code=404,
                        detail="No token found. Please provide a token or authenticate first.",
                    )

        # Kiểm tra quyền của token
        required_permissions = ["ads_read"]
        permission_check = await token_manager.check_token_permissions(
            token, required_permissions
        )

        if not permission_check.has_permission:
            if permission_check.token_status == "expired":
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": "Token has expired",
                        "authentication_url": permission_check.authorization_url,
                    },
                )
            elif permission_check.token_status == "invalid":
                raise HTTPException(
                    status_code=401,
                    detail={"message": permission_check.message},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Token lacks required permissions: {', '.join(permission_check.missing_permissions)}",
                        "authentication_url": permission_check.authorization_url,
                    },
                )

        # Create Request Objects
        date_range_obj = DateRange(start_date=start_date, end_date=end_date)
        request_obj = FacebookCampaignMetricsRequest(
            ad_account_id=ad_account_id,
            campaign_ids=requested_campaign_ids,
            date_range=date_range_obj,
            metrics=requested_metrics,
            dimensions=requested_dimensions,
        )

        # Update token in service
        service.update_access_token(token)

        # Get data from service
        results = await service.get_campaign_insights(
            request=request_obj,
        )

        if not results:
            # Return empty CSV if no data
            output = StringIO()
            output.write("\ufeff")  # BOM for Excel
            output.write("No campaign data found for the specified criteria.")
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=campaign_metrics_empty.csv"
                },
            )

        # --- CSV Generation ---
        output = StringIO()
        output.write("\ufeff")  # BOM for Excel compatibility

        # Flatten data and determine headers
        flat_data = []
        all_keys = set()
        base_keys = [
            "account_id",
            "campaign_id",
            "campaign_name",
            "date_start",
            "date_stop",
        ]
        dimension_keys = set()
        metric_keys = set()

        for insight in results:
            row = insight.dict()  # Convert Pydantic model to dict
            flat_row = {}
            # Base info
            for k in base_keys:
                flat_row[k] = row.get(k)
                all_keys.add(k)
            # Dimensions
            if row.get("dimensions"):
                for k, v in row["dimensions"].items():
                    flat_row[k] = v
                    all_keys.add(k)
                    dimension_keys.add(k)
            # Metrics
            if row.get("metrics"):
                for k, v in row["metrics"].items():
                    flat_row[k] = v
                    all_keys.add(k)
                    metric_keys.add(k)
            flat_data.append(flat_row)

        # Define header order: base, dimensions (sorted), metrics (sorted)
        fieldnames = (
            list(base_keys)
            + sorted(list(dimension_keys))
            + sorted(list(metric_keys))
        )

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_data)
        # --- End CSV Generation ---

        output.seek(0)
        filename = (
            f"campaign_metrics_{ad_account_id}_{start_date}_{end_date}.csv"
        )
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return StreamingResponse(
            iter([output.getvalue()]), media_type="text/csv", headers=headers
        )

    except FacebookRequestError as e:
        logger.error(
            f"Facebook API error in campaign_metrics_csv endpoint: {e.api_error_message()}",
            exc_info=True,
        )
        error_message = f"Facebook API Error: {e.api_error_message()} (Code: {e.api_error_code()}, Subcode: {e.api_error_subcode()})"
        return StreamingResponse(
            iter([error_message]), media_type="text/plain", status_code=400
        )
    except HTTPException as e:
        # Forward HTTP exceptions raised earlier
        raise e
    except Exception as e:
        logger.error(
            f"Unexpected error in campaign_metrics_csv endpoint: {e}",
            exc_info=True,
        )
        error_message = f"Internal server error: {str(e)}"
        return StreamingResponse(
            iter([error_message]), media_type="text/plain", status_code=500
        )


@router.get("/post_metrics", response_model=FacebookMetricsResponse)
async def get_post_metrics(
    page_id: str = Query(..., description="ID của trang Facebook"),
    post_ids: str = Query(
        None, description="Danh sách post IDs (phân cách bằng dấu phẩy)"
    ),
    metrics: str = Query(
        "impressions,reach,engaged_users,reactions",
        description="Danh sách metrics (phân cách bằng dấu phẩy)",
    ),
    since_date: str = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"),
    until_date: str = Query(..., description="Ngày kết thúc (YYYY-MM-DD)"),
    token: Optional[str] = Query(
        None,
        description="Facebook access token with pages_read_engagement permission. If not provided, will try to use page token from storage.",
    ),
    service: FacebookAdsService = Depends(get_facebook_service),
):
    """
    Lấy metrics của posts từ Facebook

    Args:
        page_id: ID của trang Facebook
        post_ids: Danh sách post IDs (phân cách bằng dấu phẩy)
        metrics: Danh sách metrics (phân cách bằng dấu phẩy)
        since_date: Ngày bắt đầu (YYYY-MM-DD)
        until_date: Ngày kết thúc (YYYY-MM-DD)
        token: Facebook access token. If not provided, will try to use page token from storage.
    """
    try:
        # Parse post_ids
        post_id_list = None
        if post_ids:
            post_id_list = post_ids.split(",")

        # Parse metrics
        metric_list = metrics.split(",")

        # Validate metrics
        valid_metrics = [m for m in metric_list if m in AVAILABLE_METRICS]
        if not valid_metrics:
            raise HTTPException(
                status_code=400, detail="No valid metrics provided"
            )

        # Validate dates
        try:
            start_date = datetime.strptime(since_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(until_date, "%Y-%m-%d").date()

            today = datetime.now().date()
            if start_date > today:
                raise HTTPException(
                    status_code=400, detail="Start date cannot be in the future"
                )

            if end_date > today:
                raise HTTPException(
                    status_code=400, detail="End date cannot be in the future"
                )

            if end_date < start_date:
                raise HTTPException(
                    status_code=400, detail="End date must be after start date"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Nếu không có token được cung cấp, thử lấy từ storage
        if not token:
            token = await token_manager.load_token()
            if not token:
                raise HTTPException(
                    status_code=404,
                    detail="No token found. Please provide a token or use /auth/facebook/callback endpoint to authenticate.",
                )

        # Kiểm tra quyền của token
        required_permissions = ["pages_read_engagement"]
        permission_check = await token_manager.check_token_permissions(
            token, required_permissions
        )

        if not permission_check.has_permission:
            if permission_check.token_status == "expired":
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": "Token has expired",
                        "authentication_url": permission_check.authorization_url,
                    },
                )
            elif permission_check.token_status == "invalid":
                raise HTTPException(
                    status_code=401,
                    detail={"message": permission_check.message},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Token lacks required permissions: {', '.join(permission_check.missing_permissions)}",
                        "authentication_url": permission_check.authorization_url,
                    },
                )

        # Tạo date range
        date_range = DateRange(start_date=start_date, end_date=end_date)

        # Update token in service
        service.update_access_token(token)

        # Get post metrics
        result = await service.get_post_insights(
            page_id=page_id,
            post_ids=post_id_list,
            date_range=date_range,
            metrics=valid_metrics,
        )

        # Trả về response
        return FacebookMetricsResponse(
            success=True,
            message="Post metrics retrieved successfully",
            data=result["data"],
            summary=result["summary"],
        )
    except FacebookRequestError as e:
        return FacebookMetricsResponse(
            success=False,
            message=f"Facebook API Error: {e.api_error_message()} (Code: {e.api_error_code()}, Subcode: {e.api_error_subcode()})",
            data=[],
            summary={},
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return FacebookMetricsResponse(
            success=False,
            message=f"Error retrieving post metrics: {str(e)}",
            data=[],
            summary={},
        )


@router.get(
    "/post_metrics_csv",
    response_class=StreamingResponse,
    summary="Get Facebook Post Insights as CSV",
    description="Retrieves insights metrics for posts on a Facebook Page and returns the data as a CSV file.",
    tags=["Facebook Metrics", "CSV Export"],
)
async def get_post_metrics_csv(
    page_id: str = Query(..., description="ID of the Facebook Page."),
    metrics: str = Query(
        "post_impressions,post_reach,post_engaged_users",  # Default example
        description="Comma-separated list of post metrics to retrieve.",
    ),
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)."),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)."),
    token: Optional[str] = Query(
        None,
        description="Facebook access token with pages_read_engagement permission. If not provided, will try to use page token from storage.",
    ),
    service: FacebookAdsService = Depends(get_facebook_service),
):
    """Fetches Facebook post insights and returns as CSV.
    Retrieves posts created within the specified date range."""

    logger.info(f"Received request for post metrics CSV for page: {page_id}")

    # Validate metrics
    requested_metrics = [m.strip() for m in metrics.split(",") if m.strip()]
    invalid_metrics = [
        m for m in requested_metrics if m not in AVAILABLE_METRICS
    ]
    if invalid_metrics:
        logger.warning(
            f"Request rejected due to invalid post metrics: {invalid_metrics}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metrics: {invalid_metrics}. Available: {AVAILABLE_METRICS}",
        )
    if not requested_metrics:
        raise HTTPException(status_code=400, detail="No metrics provided.")

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be before start date."
        )

    today = datetime.now().date()
    if start_date > today:
        raise HTTPException(
            status_code=400, detail="Start date cannot be in the future."
        )

    if end_date > today:
        raise HTTPException(
            status_code=400, detail="End date cannot be in the future."
        )

    try:
        # Nếu không có token được cung cấp, thử lấy từ storage
        if not token:
            token = await token_manager.load_token()
            if not token:
                raise HTTPException(
                    status_code=404,
                    detail="No token found. Please provide a token or use /auth/facebook/callback endpoint to authenticate.",
                )

        # Kiểm tra quyền của token
        required_permissions = ["pages_read_engagement"]
        permission_check = await token_manager.check_token_permissions(
            token, required_permissions
        )

        if not permission_check.has_permission:
            if permission_check.token_status == "expired":
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": "Token has expired",
                        "authentication_url": permission_check.authorization_url,
                    },
                )
            elif permission_check.token_status == "invalid":
                raise HTTPException(
                    status_code=401,
                    detail={"message": permission_check.message},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Token lacks required permissions: {', '.join(permission_check.missing_permissions)}",
                        "authentication_url": permission_check.authorization_url,
                    },
                )

        date_range_obj = DateRange(start_date=start_date, end_date=end_date)

        # Update token in service
        service.update_access_token(token)

        # Get data from service
        results = await service.get_post_insights(
            page_id=page_id,
            metrics=requested_metrics,
            date_range=date_range_obj,
        )

        if not results:
            output = StringIO()
            output.write("\ufeff")  # BOM
            output.write("No post data found for the specified criteria.")
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=post_metrics_empty.csv"
                },
            )

        # --- CSV Generation ---
        output = StringIO()
        output.write("\ufeff")  # BOM

        flat_data = []
        metric_keys = set(requested_metrics)
        base_keys = ["post_id", "created_time", "message", "type"]

        for insight in results:
            row = insight.dict()
            flat_row = {}
            for k in base_keys:
                flat_row[k] = row.get(k)
            # Flatten metrics
            for k in requested_metrics:
                flat_row[k] = row.get("metrics", {}).get(k)
            flat_data.append(flat_row)

        # Define header order
        fieldnames = base_keys + requested_metrics  # Use requested order

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_MINIMAL,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(flat_data)
        # --- End CSV Generation ---

        output.seek(0)
        filename = f"post_metrics_{page_id}_{start_date}_{end_date}.csv"
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return StreamingResponse(
            iter([output.getvalue()]), media_type="text/csv", headers=headers
        )

    except HTTPException as http_exc:
        raise http_exc
    except FacebookRequestError as fb_exc:
        logger.error(
            f"Facebook API error in /post_metrics_csv endpoint: {fb_exc}",
            exc_info=True,
        )
        err_msg = f"Facebook API Error: {fb_exc.api_error_message() or 'Unknown Facebook error'}"
        return StreamingResponse(
            iter([err_msg]), media_type="text/plain", status_code=400
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in /post_metrics_csv endpoint: {e}",
            exc_info=True,
        )
        err_msg = f"Internal server error: {str(e)}"
        return StreamingResponse(
            iter([err_msg]), media_type="text/plain", status_code=500
        )


@router.get("/reel_metrics", response_model=FacebookMetricsResponse)
async def get_reel_metrics(
    page_id: str = Query(..., description="ID của trang Facebook"),
    reel_ids: str = Query(
        None, description="Danh sách reel IDs (phân cách bằng dấu phẩy)"
    ),
    metrics: str = Query(
        ",".join(DEFAULT_REEL_METRICS),
        description="Danh sách metrics (phân cách bằng dấu phẩy)",
    ),
    since_date: str = Query(..., description="Ngày bắt đầu (YYYY-MM-DD)"),
    until_date: str = Query(..., description="Ngày kết thúc (YYYY-MM-DD)"),
    token: Optional[str] = Query(
        None,
        description="Facebook access token with pages_read_engagement permission. If not provided, will try to use page token from storage.",
    ),
    service: FacebookAdsService = Depends(get_facebook_service),
):
    """
    Lấy metrics của reels từ Facebook

    Args:
        page_id: ID của trang Facebook
        reel_ids: Danh sách reel IDs (phân cách bằng dấu phẩy)
        metrics: Danh sách metrics (phân cách bằng dấu phẩy)
        since_date: Ngày bắt đầu (YYYY-MM-DD)
        until_date: Ngày kết thúc (YYYY-MM-DD)
        token: Facebook access token. If not provided, will try to use page token from storage.
    """
    try:
        # Parse reel_ids
        reel_id_list = None
        if reel_ids:
            reel_id_list = reel_ids.split(",")

        # Parse metrics
        metric_list = metrics.split(",")

        # Validate metrics
        valid_metrics = [m for m in metric_list if m in AVAILABLE_REEL_METRICS]
        if not valid_metrics:
            raise HTTPException(
                status_code=400, detail="No valid metrics provided"
            )

        # Validate dates
        try:
            start_date = datetime.strptime(since_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(until_date, "%Y-%m-%d").date()

            today = datetime.now().date()
            if start_date > today:
                raise HTTPException(
                    status_code=400, detail="Start date cannot be in the future"
                )

            if end_date > today:
                raise HTTPException(
                    status_code=400, detail="End date cannot be in the future"
                )

            if end_date < start_date:
                raise HTTPException(
                    status_code=400, detail="End date must be after start date"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Nếu không có token được cung cấp, thử lấy từ storage
        if not token:
            token = await token_manager.load_token()
            if not token:
                raise HTTPException(
                    status_code=404,
                    detail="No token found. Please provide a token or use /auth/facebook/callback endpoint to authenticate.",
                )

        # Kiểm tra quyền của token
        required_permissions = ["pages_read_engagement"]
        permission_check = await token_manager.check_token_permissions(
            token, required_permissions
        )

        if not permission_check.has_permission:
            if permission_check.token_status == "expired":
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": "Token has expired",
                        "authentication_url": permission_check.authorization_url,
                    },
                )
            elif permission_check.token_status == "invalid":
                raise HTTPException(
                    status_code=401,
                    detail={"message": permission_check.message},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Token lacks required permissions: {', '.join(permission_check.missing_permissions)}",
                        "authentication_url": permission_check.authorization_url,
                    },
                )

        # Tạo date range
        date_range = DateRange(start_date=start_date, end_date=end_date)

        # Update token in service
        service.update_access_token(token)

        # Get reel metrics
        result = await service.get_reel_insights(
            page_id=page_id,
            reel_ids=reel_id_list,
            date_range=date_range,
            metrics=valid_metrics,
        )

        # Trả về response
        return FacebookMetricsResponse(
            success=True,
            message="Reel metrics retrieved successfully",
            data=result["data"],
            summary=result["summary"],
        )
    except FacebookRequestError as e:
        return FacebookMetricsResponse(
            success=False,
            message=f"Facebook API Error: {e.api_error_message()} (Code: {e.api_error_code()}, Subcode: {e.api_error_subcode()})",
            data=[],
            summary={},
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        return FacebookMetricsResponse(
            success=False,
            message=f"Error retrieving reel metrics: {str(e)}",
            data=[],
            summary={},
        )


@router.get("/reel_metrics_csv")
async def get_reel_metrics_csv(
    page_id: str = Query(..., description="ID of the Facebook Page."),
    metrics: str = Query(
        ",".join(DEFAULT_REEL_METRICS),
        description="Comma-separated list of reel/video metrics.",
    ),
    start_date: date = Query(
        ..., description="Start date (YYYY-MM-DD) for reel creation time."
    ),
    end_date: date = Query(
        ..., description="End date (YYYY-MM-DD) for reel creation time."
    ),
    token: Optional[str] = Query(
        None,
        description="Facebook access token with pages_read_engagement permission. If not provided, will try to use page token from storage.",
    ),
    service: FacebookAdsService = Depends(get_facebook_service),
):
    """
    Fetches Facebook reel insights and returns as CSV.
    Retrieves reels created within the specified date range.
    """
    logger.info(f"Received request for reel metrics CSV for page: {page_id}")

    # Validate metrics
    requested_metrics = [m.strip() for m in metrics.split(",") if m.strip()]
    invalid_metrics = [
        m for m in requested_metrics if m not in AVAILABLE_REEL_METRICS
    ]
    if invalid_metrics:
        logger.warning(
            f"Request rejected due to invalid reel metrics: {invalid_metrics}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metrics: {invalid_metrics}. Available: {AVAILABLE_REEL_METRICS}",
        )
    if not requested_metrics:
        raise HTTPException(status_code=400, detail="No metrics provided.")

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be before start date."
        )

    today = datetime.now().date()
    if start_date > today:
        raise HTTPException(
            status_code=400, detail="Start date cannot be in the future."
        )

    if end_date > today:
        raise HTTPException(
            status_code=400, detail="End date cannot be in the future."
        )

    try:
        # Nếu không có token được cung cấp, thử lấy từ storage
        if not token:
            token = await token_manager.load_token()
            if not token:
                raise HTTPException(
                    status_code=404,
                    detail="No token found. Please provide a token or use /auth/facebook/callback endpoint to authenticate.",
                )

        # Kiểm tra quyền của token
        required_permissions = ["pages_read_engagement"]
        permission_check = await token_manager.check_token_permissions(
            token, required_permissions
        )

        if not permission_check.has_permission:
            if permission_check.token_status == "expired":
                raise HTTPException(
                    status_code=401,
                    detail={
                        "message": "Token has expired",
                        "authentication_url": permission_check.authorization_url,
                    },
                )
            elif permission_check.token_status == "invalid":
                raise HTTPException(
                    status_code=401,
                    detail={"message": permission_check.message},
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": f"Token lacks required permissions: {', '.join(permission_check.missing_permissions)}",
                        "authentication_url": permission_check.authorization_url,
                    },
                )

        date_range_obj = DateRange(start_date=start_date, end_date=end_date)

        # Update token in service
        service.update_access_token(token)

        # Get data from service
        results = await service.get_reel_insights(
            page_id=page_id,
            metrics=requested_metrics,
            date_range=date_range_obj,
        )

        if not results:
            output = StringIO()
            output.write("\ufeff")  # BOM for Excel
            output.write("No reel data found for the specified criteria.")
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=reel_metrics_empty.csv"
                },
            )

        # Create CSV
        output = StringIO()
        output.write("\ufeff")  # BOM for Excel

        # Extract all possible fields for the header
        base_fields = ["reel_id", "created_time", "title", "description"]
        fields = base_fields + requested_metrics

        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()

        # Write data rows
        for reel in results:
            row = {
                "reel_id": reel.reel_id,
                "created_time": reel.created_time,
                "title": reel.title,
                "description": reel.description,
            }

            # Add metrics
            for metric in requested_metrics:
                row[metric] = reel.metrics.get(metric, "")

            writer.writerow(row)

        # Return streaming response
        output.seek(0)
        filename = f"reel_metrics_{page_id}_{start_date}_{end_date}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException as http_exc:
        raise http_exc
    except FacebookRequestError as fb_exc:
        logger.error(
            f"Facebook API error in /reel_metrics_csv endpoint: {fb_exc}",
            exc_info=True,
        )
        err_msg = f"Facebook API Error: {fb_exc.api_error_message() or 'Unknown Facebook error'}"
        return StreamingResponse(
            iter([err_msg]), media_type="text/plain", status_code=400
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in /reel_metrics_csv endpoint: {e}",
            exc_info=True,
        )
        err_msg = f"Internal server error: {str(e)}"
        return StreamingResponse(
            iter([err_msg]), media_type="text/plain", status_code=500
        )


@router.get(
    "/available_metrics",
    response_model=None,
    summary="Get Available Facebook Metrics",
    description="Returns lists of available metrics that can be requested for posts, reels, and ads.",
    tags=["Facebook Utility"],
)
async def get_available_metrics(
    cache: CacheService = Depends(
        get_cache_service
    ),  # Use get_cache_service factory
):
    """
    Provides lists of available metrics for different Facebook content types.
    Uses cached data if available.
    """
    cache_key = "facebook_available_metrics"
    cached_data = await cache.get(cache_key)
    if cached_data:
        logger.info("Returning cached available metrics.")
        return cached_data

    logger.info("Generating available metrics list (not cached).")
    # In a real scenario, these lists might be dynamically generated or verified
    # For now, we return the constants directly.
    metrics_data = AVAILABLE_METRICS_DICT

    # Cache the result (long TTL, e.g., 1 day)
    await cache.set(cache_key, metrics_data, ttl=86400)

    return metrics_data


@router.get("/debug_token")
async def debug_token(
    token: str = Query(...),
    service: FacebookAdsService = Depends(get_facebook_service),
):
    """Debug a Facebook access token"""
    try:
        debug_info = await service.debug_token(token)
        return debug_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check_business_pages_access")
async def check_business_pages_access(
    business_id: str = Query(...),
    service: FacebookAdsService = Depends(get_facebook_service),
):
    """Check access to all pages in a business"""
    try:
        pages = await service.get_business_pages(business_id)
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
