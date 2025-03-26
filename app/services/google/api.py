import logging
from typing import Any, Dict, List, Optional

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from app.core.config import settings
from app.core.constants import (
    DEFAULT_GOOGLE_ADS_DIMENSIONS,
    DEFAULT_GOOGLE_ADS_METRICS,
    GOOGLE_ADS_DIMENSIONS,
    GOOGLE_ADS_METRICS,
)
from app.models.google import AdGroupInsight, AdInsight, CampaignInsight


class GoogleAdsManager:
    def __init__(self):
        self.client = None
        self.init_client()

    def init_client(self):
        """Initialize Google Ads API client"""
        try:
            self.client = GoogleAdsClient.load_from_storage(
                settings.GOOGLE_ADS_CONFIG_FILE
            )
        except Exception as e:
            logging.error(f"Failed to initialize Google Ads client: {str(e)}")
            self.client = None

    async def get_campaign_insights(
        self,
        client_id: str,
        metrics: List[str] = DEFAULT_GOOGLE_ADS_METRICS,
        dimensions: List[str] = DEFAULT_GOOGLE_ADS_DIMENSIONS,
        date_range: str = "LAST_30_DAYS",
    ) -> List[CampaignInsight]:
        """Get campaign insights from Google Ads"""
        if not self.client:
            logging.warning("Google Ads client not initialized")
            return []

        try:
            ga_service = self.client.get_service("GoogleAdsService")

            # Build query
            query = self._build_query(
                metrics, dimensions, date_range, "campaign"
            )

            # Execute query
            response = ga_service.search(customer_id=client_id, query=query)

            insights = []
            for row in response:
                campaign = row.campaign
                metrics_data = self._extract_metrics(row, metrics)
                dimensions_data = self._extract_dimensions(row, dimensions)

                insight = CampaignInsight(
                    client_id=client_id,
                    campaign_id=campaign.id,
                    campaign_name=campaign.name,
                    metrics=metrics_data,
                    dimensions=dimensions_data,
                    date_range=date_range,
                )
                insights.append(insight)

            return insights

        except GoogleAdsException as e:
            logging.error(f"Google Ads API error: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error getting campaign insights: {str(e)}")
            return []

    async def get_ad_group_insights(
        self,
        client_id: str,
        metrics: List[str] = DEFAULT_GOOGLE_ADS_METRICS,
        dimensions: List[str] = DEFAULT_GOOGLE_ADS_DIMENSIONS,
        date_range: str = "LAST_30_DAYS",
    ) -> List[AdGroupInsight]:
        """Get ad group insights from Google Ads"""
        if not self.client:
            logging.warning("Google Ads client not initialized")
            return []

        try:
            ga_service = self.client.get_service("GoogleAdsService")

            # Build query
            query = self._build_query(
                metrics, dimensions, date_range, "ad_group"
            )

            # Execute query
            response = ga_service.search(customer_id=client_id, query=query)

            insights = []
            for row in response:
                campaign = row.campaign
                ad_group = row.ad_group
                metrics_data = self._extract_metrics(row, metrics)
                dimensions_data = self._extract_dimensions(row, dimensions)

                insight = AdGroupInsight(
                    client_id=client_id,
                    campaign_id=campaign.id,
                    campaign_name=campaign.name,
                    ad_group_id=ad_group.id,
                    ad_group_name=ad_group.name,
                    metrics=metrics_data,
                    dimensions=dimensions_data,
                    date_range=date_range,
                )
                insights.append(insight)

            return insights

        except GoogleAdsException as e:
            logging.error(f"Google Ads API error: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"Error getting ad group insights: {str(e)}")
            return []

    def _build_query(
        self,
        metrics: List[str],
        dimensions: List[str],
        date_range: str,
        level: str,
    ) -> str:
        """Build Google Ads query string"""
        # Convert metric names to API format
        metrics_str = ", ".join(
            [GOOGLE_ADS_METRICS[m] for m in metrics if m in GOOGLE_ADS_METRICS]
        )
        dimensions_str = ", ".join(
            [
                GOOGLE_ADS_DIMENSIONS[d]
                for d in dimensions
                if d in GOOGLE_ADS_DIMENSIONS
            ]
        )

        # Base fields based on level
        base_fields = {
            "campaign": "campaign.id, campaign.name",
            "ad_group": "campaign.id, campaign.name, ad_group.id, ad_group.name",
            "ad": "campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group_ad.ad.id, ad_group_ad.ad.name",
        }

        # Build query
        query = f"""
            SELECT
                {base_fields[level]},
                {metrics_str},
                {dimensions_str}
            FROM {level}
            WHERE segments.date DURING {date_range}
        """

        return query

    def _extract_metrics(self, row: Any, metrics: List[str]) -> Dict[str, Any]:
        """Extract metrics from Google Ads API response"""
        results = {}
        for metric in metrics:
            if metric in GOOGLE_ADS_METRICS:
                field_path = GOOGLE_ADS_METRICS[metric].split(".")
                value = row
                for field in field_path:
                    value = getattr(value, field, None)
                results[metric] = value
        return results

    def _extract_dimensions(
        self, row: Any, dimensions: List[str]
    ) -> Dict[str, Any]:
        """Extract dimensions from Google Ads API response"""
        results = {}
        for dimension in dimensions:
            if dimension in GOOGLE_ADS_DIMENSIONS:
                field_path = GOOGLE_ADS_DIMENSIONS[dimension].split(".")
                value = row
                for field in field_path:
                    value = getattr(value, field, None)
                results[dimension] = value
        return results
