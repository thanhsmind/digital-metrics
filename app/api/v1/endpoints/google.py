from typing import List
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from io import StringIO
import csv

from app.services.google.api import GoogleAdsManager
from app.core.constants import (
    GOOGLE_ADS_METRICS,
    GOOGLE_ADS_DIMENSIONS,
    DEFAULT_GOOGLE_ADS_METRICS,
    DEFAULT_GOOGLE_ADS_DIMENSIONS
)

router = APIRouter()
google_ads_api = GoogleAdsManager()

@router.get("/campaigns_csv")
async def get_campaigns_csv(
    client_id: str = Query(..., description="ID of the Google Ads client"),
    metrics: str = Query(
        ",".join(DEFAULT_GOOGLE_ADS_METRICS),
        description="Comma-separated list of metrics"
    ),
    dimensions: str = Query(
        ",".join(DEFAULT_GOOGLE_ADS_DIMENSIONS),
        description="Comma-separated list of dimensions"
    ),
    date_range: str = Query(
        'LAST_30_DAYS',
        description="Date range for the report"
    )
):
    """Get campaign insights in CSV format"""
    try:
        # Validate metrics and dimensions
        metric_list = metrics.split(',')
        dimension_list = dimensions.split(',')
        
        valid_metrics = [m for m in metric_list if m in GOOGLE_ADS_METRICS]
        valid_dimensions = [d for d in dimension_list if d in GOOGLE_ADS_DIMENSIONS]
        
        if not valid_metrics:
            raise HTTPException(status_code=400, detail="No valid metrics provided")
            
        # Get insights
        insights = await google_ads_api.get_campaign_insights(
            client_id,
            valid_metrics,
            valid_dimensions,
            date_range
        )
        
        # Convert to CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ['client_id', 'campaign_id', 'campaign_name']
        headers.extend(valid_dimensions)
        headers.extend(valid_metrics)
        writer.writerow(headers)
        
        # Write data
        for insight in insights:
            row = [
                insight.client_id,
                insight.campaign_id,
                insight.campaign_name
            ]
            
            # Add dimensions
            for dimension in valid_dimensions:
                row.append(insight.dimensions.get(dimension, ''))
                
            # Add metrics
            for metric in valid_metrics:
                row.append(insight.metrics.get(metric, 0))
                
            writer.writerow(row)
            
        # Prepare response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename=campaign_insights_{client_id}.csv'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ad_groups_csv")
async def get_ad_groups_csv(
    client_id: str = Query(..., description="ID of the Google Ads client"),
    metrics: str = Query(
        ",".join(DEFAULT_GOOGLE_ADS_METRICS),
        description="Comma-separated list of metrics"
    ),
    dimensions: str = Query(
        ",".join(DEFAULT_GOOGLE_ADS_DIMENSIONS),
        description="Comma-separated list of dimensions"
    ),
    date_range: str = Query(
        'LAST_30_DAYS',
        description="Date range for the report"
    )
):
    """Get ad group insights in CSV format"""
    try:
        # Validate metrics and dimensions
        metric_list = metrics.split(',')
        dimension_list = dimensions.split(',')
        
        valid_metrics = [m for m in metric_list if m in GOOGLE_ADS_METRICS]
        valid_dimensions = [d for d in dimension_list if d in GOOGLE_ADS_DIMENSIONS]
        
        if not valid_metrics:
            raise HTTPException(status_code=400, detail="No valid metrics provided")
            
        # Get insights
        insights = await google_ads_api.get_ad_group_insights(
            client_id,
            valid_metrics,
            valid_dimensions,
            date_range
        )
        
        # Convert to CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'client_id',
            'campaign_id',
            'campaign_name',
            'ad_group_id',
            'ad_group_name'
        ]
        headers.extend(valid_dimensions)
        headers.extend(valid_metrics)
        writer.writerow(headers)
        
        # Write data
        for insight in insights:
            row = [
                insight.client_id,
                insight.campaign_id,
                insight.campaign_name,
                insight.ad_group_id,
                insight.ad_group_name
            ]
            
            # Add dimensions
            for dimension in valid_dimensions:
                row.append(insight.dimensions.get(dimension, ''))
                
            # Add metrics
            for metric in valid_metrics:
                row.append(insight.metrics.get(metric, 0))
                
            writer.writerow(row)
            
        # Prepare response
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename=ad_group_insights_{client_id}.csv'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available_metrics")
async def get_available_metrics():
    """Get list of available Google Ads metrics"""
    return {
        "metrics": list(GOOGLE_ADS_METRICS.keys()),
        "default_metrics": DEFAULT_GOOGLE_ADS_METRICS
    }

@router.get("/available_dimensions")
async def get_available_dimensions():
    """Get list of available Google Ads dimensions"""
    return {
        "dimensions": list(GOOGLE_ADS_DIMENSIONS.keys()),
        "default_dimensions": DEFAULT_GOOGLE_ADS_DIMENSIONS
    } 