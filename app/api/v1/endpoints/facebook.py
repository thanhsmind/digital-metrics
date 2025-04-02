import csv
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
from app.core.dependencies import get_facebook_service, oauth2_scheme
from app.models import (
    DateRange,
    FacebookCampaignMetricsRequest,
    FacebookMetricsResponse,
    PostInsight,
)
from app.services.cache_service import CacheService
from app.services.facebook_ads import FacebookAdsService
from app.utils.csv_utils import generate_csv_response

router = APIRouter()


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
    service: FacebookAdsService = Depends(get_facebook_service),
    token: str = Depends(oauth2_scheme),
):
    """
    Get post insights for all pages of a business in CSV format.

    - **business_id**: The ID of the target Facebook Business Manager.
    - **metrics**: Comma-separated list of metrics to retrieve.
    - **since_date**: Start date for filtering posts.
    - **until_date**: End date for filtering posts.
    """
    if until_date < since_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be before start date."
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
        insights: List[PostInsight] = await service.get_business_post_insights(
            business_id=business_id,
            metrics=metrics_list,
            date_range=date_range_obj,
            access_token=token,
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
    summary="Get Business Post & Reel Insights as CSV",
    description="Retrieves both post and reel insights for all pages associated with a Facebook Business and returns the combined data as a CSV file.",
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
        ..., description="Start date (YYYY-MM-DD) for content creation time."
    ),
    until_date: date = Query(
        ..., description="End date (YYYY-MM-DD) for content creation time."
    ),
    service: FacebookAdsService = Depends(get_facebook_service),
    token: str = Depends(oauth2_scheme),
):
    """
    Get combined post and reel insights for all pages of a business in CSV format.

    - **business_id**: The ID of the target Facebook Business Manager.
    - **post_metrics**: Comma-separated list of metrics for regular posts.
    - **reel_metrics**: Comma-separated list of metrics for reels.
    - **since_date**: Start date for filtering content.
    - **until_date**: End date for filtering content.
    """
    # Validate dates
    if until_date < since_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be before start date."
        )

    # Parse and validate post metrics
    post_metrics_list = []
    if post_metrics:
        raw_post_metrics = [
            m.strip() for m in post_metrics.split(",") if m.strip()
        ]
        if raw_post_metrics:
            valid_post_metrics = [
                m for m in raw_post_metrics if m in AVAILABLE_METRICS
            ]
            post_metrics_list = valid_post_metrics
            invalid_post = [
                m for m in raw_post_metrics if m not in AVAILABLE_METRICS
            ]
            if invalid_post:
                print(
                    f"Warning: Ignoring invalid post metrics: {', '.join(invalid_post)}"
                )

    # Parse and validate reel metrics
    reel_metrics_list = []
    if reel_metrics:
        raw_reel_metrics = [
            m.strip() for m in reel_metrics.split(",") if m.strip()
        ]
        if raw_reel_metrics:
            valid_reel_metrics = [
                m for m in raw_reel_metrics if m in AVAILABLE_REEL_METRICS
            ]
            reel_metrics_list = valid_reel_metrics
            invalid_reel = [
                m for m in raw_reel_metrics if m not in AVAILABLE_REEL_METRICS
            ]
            if invalid_reel:
                print(
                    f"Warning: Ignoring invalid reel metrics: {', '.join(invalid_reel)}"
                )

    if not post_metrics_list and not reel_metrics_list:
        raise HTTPException(
            status_code=400,
            detail="No valid post or reel metrics provided. Please check available metrics.",
        )

    date_range_obj = DateRange(start_date=since_date, end_date=until_date)

    try:
        # Call the service method
        post_insights, reel_insights = (
            await service.get_all_business_posts_and_reels_insights(
                business_id=business_id,
                post_metrics=post_metrics_list,
                reel_metrics=reel_metrics_list,
                date_range=date_range_obj,
                access_token=token,
            )
        )

        # Combine and prepare data for CSV
        combined_data = []
        for post in post_insights:
            item = post.dict()
            item["content_type"] = "Post"
            combined_data.append(item)
        for reel in reel_insights:
            item = reel.dict()
            item["content_type"] = "Reel"
            # Keep video_id distinct
            combined_data.append(item)

        # Generate CSV response using the utility function
        filename = f"business_{business_id}_all_insights_{since_date}_to_{until_date}.csv"
        return await generate_csv_response(
            data=combined_data, filename=filename
        )

    except FacebookRequestError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Facebook API Error: {', '.join(e.args)} (Code: {e.api_error_code()}, Subcode: {e.api_error_subcode()})",  # Adjust detail
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(
            f"Error generating combined business insights CSV for {business_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Internal server error processing request."
        )


@router.get("/campaign_metrics", response_model=FacebookMetricsResponse)
async def get_campaign_metrics(
    ad_account_id: str = Query(..., description="ID của tài khoản quảng cáo"),
    campaign_ids: str = Query(
        None, description="Danh sách campaign IDs (phân cách bằng dấu phẩy)"
    ),
    metrics: str = Query(
        "spend,impressions,reach,clicks,ctr",
        description="Comma-separated list of metrics",
    ),
    since_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    until_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    access_token: str = Query(..., description="Facebook access token"),
):
    """
    Lấy metrics của campaigns từ Facebook Ads

    Args:
        ad_account_id: ID của tài khoản quảng cáo
        campaign_ids: Danh sách campaign IDs (phân cách bằng dấu phẩy)
        metrics: Danh sách metrics (phân cách bằng dấu phẩy)
        since_date: Ngày bắt đầu (YYYY-MM-DD)
        until_date: Ngày kết thúc (YYYY-MM-DD)
        access_token: Facebook access token

    Returns:
        FacebookMetricsResponse chứa metrics data và summary
    """
    try:
        # Parse campaign_ids
        campaign_id_list = None
        if campaign_ids:
            campaign_id_list = campaign_ids.split(",")

        # Parse metrics
        metric_list = metrics.split(",")

        # Validate dates
        try:
            start_date = datetime.strptime(since_date, "%Y-%m-%d")
            end_date = datetime.strptime(until_date, "%Y-%m-%d")
            if end_date < start_date:
                raise HTTPException(
                    status_code=400, detail="End date must be after start date"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Tạo request object
        date_range = DateRange(start_date=start_date, end_date=end_date)

        # Get campaign metrics
        result = await get_facebook_service().get_campaign_metrics(
            ad_account_id=ad_account_id,
            campaign_ids=campaign_id_list,
            date_range=date_range,
            metrics=metric_list,
            access_token=access_token,
        )

        # Trả về response
        return FacebookMetricsResponse(
            success=True,
            message="Campaign metrics retrieved successfully",
            data=result["data"],
            summary=result["summary"],
        )
    except Exception as e:
        return FacebookMetricsResponse(
            success=False,
            message=f"Error retrieving campaign metrics: {str(e)}",
            data=[],
            summary={},
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
    service: FacebookAdsService = Depends(),
    token: str = Depends(
        get_placeholder_token
    ),  # Placeholder - needs ad account token logic
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

    # Create Request Objects
    date_range_obj = DateRange(start_date=start_date, end_date=end_date)
    request_obj = FacebookCampaignMetricsRequest(
        ad_account_id=ad_account_id,
        campaign_ids=requested_campaign_ids,
        date_range=date_range_obj,
        metrics=requested_metrics,
        dimensions=requested_dimensions,
    )

    try:
        # Get data from service
        results = await service.get_campaign_insights(
            request=request_obj,
            access_token=token,
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
        ordered_dimension_keys = sorted(list(dimension_keys))
        ordered_metric_keys = sorted(list(metric_keys))
        fieldnames = base_keys + ordered_dimension_keys + ordered_metric_keys
        # Ensure all keys found are included, even if not in predefined lists (optional)
        # for k in sorted(list(all_keys)):
        #     if k not in fieldnames:
        #          fieldnames.append(k)

        writer = csv.DictWriter(
            output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL
        )
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

    except HTTPException as http_exc:
        raise http_exc  # Re-raise validation errors etc.
    except FacebookRequestError as fb_exc:
        logger.error(
            f"Facebook API error in /campaign_metrics_csv endpoint: {fb_exc}",
            exc_info=True,
        )
        # Return error as text response for CSV endpoint
        err_msg = f"Facebook API Error: {fb_exc.api_error_message() or 'Unknown Facebook error'}"
        return StreamingResponse(
            iter([err_msg]), media_type="text/plain", status_code=400
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in /campaign_metrics_csv endpoint: {e}",
            exc_info=True,
        )
        return StreamingResponse(
            iter(["Internal server error generating CSV."]),
            media_type="text/plain",
            status_code=500,
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
    access_token: str = Query(..., description="Facebook access token"),
):
    """
    Lấy metrics của posts từ Facebook

    Args:
        page_id: ID của trang Facebook
        post_ids: Danh sách post IDs (phân cách bằng dấu phẩy)
        metrics: Danh sách metrics (phân cách bằng dấu phẩy)
        since_date: Ngày bắt đầu (YYYY-MM-DD)
        until_date: Ngày kết thúc (YYYY-MM-DD)
        access_token: Facebook access token

    Returns:
        FacebookMetricsResponse chứa metrics data và summary
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
            start_date = datetime.strptime(since_date, "%Y-%m-%d")
            end_date = datetime.strptime(until_date, "%Y-%m-%d")
            if end_date < start_date:
                raise HTTPException(
                    status_code=400, detail="End date must be after start date"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Tạo date range
        date_range = DateRange(start_date=start_date, end_date=end_date)

        # Get post metrics
        result = await get_facebook_service().get_post_metrics(
            page_id=page_id,
            post_ids=post_id_list,
            date_range=date_range,
            metrics=valid_metrics,
            access_token=access_token,
        )

        # Trả về response
        return FacebookMetricsResponse(
            success=True,
            message="Post metrics retrieved successfully",
            data=result["data"],
            summary=result["summary"],
        )
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
    service: FacebookAdsService = Depends(),
    token: str = Depends(get_placeholder_token),
):
    """Fetches Facebook post insights and returns as CSV."""
    logger.info(f"Received request for post metrics CSV for page: {page_id}")

    # Validate metrics
    requested_metrics = [m.strip() for m in metrics.split(",") if m.strip()]
    invalid_metrics = [
        m for m in requested_metrics if m not in AVAILABLE_POST_METRICS
    ]
    if invalid_metrics:
        logger.warning(
            f"Request rejected due to invalid post metrics: {invalid_metrics}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metrics: {invalid_metrics}. Available: {AVAILABLE_POST_METRICS}",
        )
    if not requested_metrics:
        raise HTTPException(status_code=400, detail="No metrics provided.")

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be before start date."
        )

    date_range_obj = DateRange(start_date=start_date, end_date=end_date)

    try:
        # Get data from service
        results = await service.get_post_insights(
            page_id=page_id,
            metrics=requested_metrics,
            date_range=date_range_obj,
            access_token=token,
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
        return StreamingResponse(
            iter(["Internal server error generating CSV."]),
            media_type="text/plain",
            status_code=500,
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
    access_token: str = Query(..., description="Facebook access token"),
):
    """
    Lấy metrics của reels từ Facebook

    Args:
        page_id: ID của trang Facebook
        reel_ids: Danh sách reel IDs (phân cách bằng dấu phẩy)
        metrics: Danh sách metrics (phân cách bằng dấu phẩy)
        since_date: Ngày bắt đầu (YYYY-MM-DD)
        until_date: Ngày kết thúc (YYYY-MM-DD)
        access_token: Facebook access token

    Returns:
        FacebookMetricsResponse chứa metrics data và summary
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
            start_date = datetime.strptime(since_date, "%Y-%m-%d")
            end_date = datetime.strptime(until_date, "%Y-%m-%d")
            if end_date < start_date:
                raise HTTPException(
                    status_code=400, detail="End date must be after start date"
                )
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Tạo date range
        date_range = DateRange(start_date=start_date, end_date=end_date)

        # Get reel metrics
        result = await get_facebook_service().get_reel_metrics(
            page_id=page_id,
            reel_ids=reel_id_list,
            date_range=date_range,
            metrics=valid_metrics,
            access_token=access_token,
        )

        # Trả về response
        return FacebookMetricsResponse(
            success=True,
            message="Reel metrics retrieved successfully",
            data=result["data"],
            summary=result["summary"],
        )
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
    service: FacebookAdsService = Depends(),
    token: str = Depends(get_placeholder_token),
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
        raise HTTPException(status_code=400, detail="No reel metrics provided.")

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="End date cannot be before start date."
        )

    date_range_obj = DateRange(start_date=start_date, end_date=end_date)

    try:
        # Get data from service
        results = await service.get_reel_insights(
            page_id=page_id,
            metrics=requested_metrics,
            date_range=date_range_obj,
            access_token=token,
        )

        if not results:
            output = StringIO()
            output.write("\ufeff")  # BOM
            output.write("No reel data found for the specified criteria.")
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=reel_metrics_empty.csv"
                },
            )

        # --- CSV Generation ---
        output = StringIO()
        output.write("\ufeff")  # BOM

        flat_data = []
        metric_keys = set(requested_metrics)
        # Base keys from VideoInsight model
        base_keys = ["video_id", "created_time", "title", "description"]

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
        filename = f"reel_metrics_{page_id}_{start_date}_{end_date}.csv"
        headers = {"Content-Disposition": f"attachment; filename={filename}"}
        return StreamingResponse(
            iter([output.getvalue()]), media_type="text/csv", headers=headers
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
        return StreamingResponse(
            iter(["Internal server error generating CSV."]),
            media_type="text/plain",
            status_code=500,
        )


@router.get(
    "/available_metrics",
    response_model=Dict[str, List[str]],
    summary="Get Available Facebook Metrics",
    description="Returns lists of available metrics that can be requested for posts, reels, and ads.",
    tags=["Facebook Utility"],
)
async def get_available_metrics(
    cache: CacheService = Depends(),  # Inject cache service
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
async def debug_token(token: str = Query(...)):
    """Debug a Facebook access token"""
    try:
        debug_info = await get_facebook_service().debug_token(token)
        return debug_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check_business_pages_access")
async def check_business_pages_access(business_id: str = Query(...)):
    """Check access to all pages in a business"""
    try:
        pages = await get_facebook_service().get_business_pages(business_id)
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
