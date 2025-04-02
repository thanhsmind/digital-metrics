import json
import logging
import os
from datetime import datetime, timedelta
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
from app.utils.encryption import TokenEncryption


class GoogleAdsManager:
    def __init__(self):
        self.client = None
        self.token_file = settings.GOOGLE_TOKEN_FILE
        self.tokens_data = {"client_tokens": {}}
        # Đảm bảo thư mục tồn tại
        self._ensure_token_dir_exists()
        self._load_tokens()
        self.init_client()

    def _ensure_token_dir_exists(self):
        """Đảm bảo thư mục lưu trữ token tồn tại"""
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)

    def _load_tokens(self):
        """Tải tokens từ file JSON"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r") as f:
                    self.tokens_data = json.load(f)
                logging.info(f"Loaded tokens from {self.token_file}")
            else:
                self.tokens_data = {"client_tokens": {}}
                logging.info(
                    f"No token file found at {self.token_file}, created new token store"
                )
        except Exception as e:
            logging.error(f"Error loading tokens from file: {str(e)}")
            self.tokens_data = {"client_tokens": {}}

    def _save_tokens(self):
        """Lưu tokens vào file JSON"""
        try:
            with open(self.token_file, "w") as f:
                json.dump(self.tokens_data, f, indent=2)
            logging.info(f"Saved tokens to {self.token_file}")
            return True
        except Exception as e:
            logging.error(f"Error saving tokens to file: {str(e)}")
            return False

    def store_client_token(self, client_id: str, token_data: Dict[str, Any]):
        """Lưu token cho client vào storage"""
        try:
            # Mã hóa token trước khi lưu
            token_json = json.dumps(token_data)
            encrypted_token = TokenEncryption.encrypt_token(token_json)

            if not encrypted_token:
                logging.error(
                    "Failed to encrypt token, storing without encryption"
                )
                client_data = {"encrypted": False, "data": token_data}
            else:
                client_data = {"encrypted": True, "token": encrypted_token}

            # Thêm timestamp
            client_data["updated_at"] = datetime.now().isoformat()

            # Lưu vào dictionary
            self.tokens_data["client_tokens"][client_id] = client_data

            # Lưu vào file
            self._save_tokens()
            return True
        except Exception as e:
            logging.error(f"Error storing client token: {str(e)}")
            return False

    def get_client_token(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Lấy token cho client từ storage"""
        try:
            if (
                "client_tokens" not in self.tokens_data
                or client_id not in self.tokens_data["client_tokens"]
            ):
                return None

            token_data = self.tokens_data["client_tokens"][client_id]

            # Kiểm tra xem token có mã hóa không
            if token_data.get("encrypted", False):
                encrypted_token = token_data.get("token")
                if not encrypted_token:
                    logging.error(
                        f"Encrypted token for client {client_id} not found"
                    )
                    return None

                decrypted_data = TokenEncryption.decrypt_token(encrypted_token)
                if not decrypted_data:
                    logging.error(
                        f"Failed to decrypt token for client {client_id}"
                    )
                    return None

                return json.loads(decrypted_data)
            else:
                # Token lưu dưới dạng raw dict
                return token_data.get("data", {})
        except Exception as e:
            logging.error(f"Error retrieving client token: {str(e)}")
            return None

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
