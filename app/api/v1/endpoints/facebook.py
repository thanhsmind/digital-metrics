from typing import List
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from io import StringIO
import csv

from app.services.facebook.api import FacebookApiManager
from app.core.constants import AVAILABLE_METRICS, AVAILABLE_REEL_METRICS, DEFAULT_REEL_METRICS

router = APIRouter()
facebook_api = FacebookApiManager()

@router.get("/business_post_insights_csv")
async def get_business_post_insights_csv(
    business_id: str = Query(..., description="ID of the business"),
    metrics: str = Query(
        "impressions,reach,engaged_users,reactions",
        description="Comma-separated list of metrics"
    ),
    since_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    until_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get post insights for a business in CSV format"""
    try:
        # Validate metrics
        metric_list = metrics.split(',')
        valid_metrics = [m for m in metric_list if m in AVAILABLE_METRICS]
        
        if not valid_metrics:
            raise HTTPException(status_code=400, detail="No valid metrics provided")
            
        # Get insights
        insights = await facebook_api.get_business_post_insights(
            business_id,
            valid_metrics,
            since_date,
            until_date
        )
        
        # Convert to CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ['post_id', 'created_time', 'message', 'type'] + valid_metrics
        writer.writerow(headers)
        
        # Write data
        for insight in insights:
            row = [
                insight.post_id,
                insight.created_time,
                insight.message,
                insight.type
            ]
            for metric in valid_metrics:
                row.append(insight.metrics.get(metric, 0))
            writer.writerow(row)
            
        # Prepare response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename=business_post_insights_{business_id}.csv'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/business_posts_and_reels_insights_csv")
async def get_business_posts_and_reels_insights_csv(
    business_id: str = Query(..., description="ID of the business"),
    post_metrics: str = Query(
        "impressions,reach,engaged_users",
        description="Comma-separated list of post metrics"
    ),
    reel_metrics: str = Query(
        ",".join(DEFAULT_REEL_METRICS),
        description="Comma-separated list of reel metrics"
    ),
    since_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    until_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get combined post and reel insights for a business in CSV format"""
    try:
        # Validate metrics
        post_metric_list = post_metrics.split(',')
        reel_metric_list = reel_metrics.split(',')
        
        valid_post_metrics = [m for m in post_metric_list if m in AVAILABLE_METRICS]
        valid_reel_metrics = [m for m in reel_metric_list if m in AVAILABLE_REEL_METRICS]
        
        if not valid_post_metrics and not valid_reel_metrics:
            raise HTTPException(status_code=400, detail="No valid metrics provided")
            
        # Get insights
        insights = await facebook_api.get_all_business_posts_and_reels_insights(
            business_id,
            valid_post_metrics,
            valid_reel_metrics,
            since_date,
            until_date
        )
        
        # Convert to CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ['post_id', 'created_time', 'message', 'type']
        if valid_post_metrics:
            headers.extend(valid_post_metrics)
        if valid_reel_metrics:
            headers.extend(valid_reel_metrics)
        writer.writerow(headers)
        
        # Write data
        for insight in insights:
            row = [
                insight.post_id,
                insight.created_time,
                insight.message,
                insight.type
            ]
            
            # Add post metrics
            for metric in valid_post_metrics:
                row.append(insight.metrics.get(metric, 0))
                
            # Add reel metrics
            for metric in valid_reel_metrics:
                row.append(insight.metrics.get(metric, 0))
                
            writer.writerow(row)
            
        # Prepare response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename=business_insights_{business_id}.csv'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available_metrics")
async def get_available_metrics():
    """Get list of available metrics"""
    return {
        "post_metrics": list(AVAILABLE_METRICS.keys()),
        "reel_metrics": list(AVAILABLE_REEL_METRICS.keys())
    }

@router.get("/debug_token")
async def debug_token(token: str = Query(...)):
    """Debug a Facebook access token"""
    try:
        debug_info = await facebook_api.debug_token(token)
        return debug_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check_business_pages_access")
async def check_business_pages_access(business_id: str = Query(...)):
    """Check access to all pages in a business"""
    try:
        pages = await facebook_api.get_business_pages(business_id)
        return pages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 