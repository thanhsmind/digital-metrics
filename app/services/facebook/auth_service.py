import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as redis_asyncio
from facebook_business.adobjects.user import User
from facebook_business.api import FacebookAdsApi
from facebook_business.exceptions import FacebookRequestError

from app.core.config import settings
from app.models.auth import (
    AuthError,
    FacebookAuthCredential,
    FacebookPageToken,
    FacebookUserToken,
    TokenValidationResponse,
)


class FacebookAuthService:
    """Service xử lý authentication với Facebook API"""

    def __init__(self):
        """Khởi tạo service với credentials từ environment"""
        self.app_id = settings.FACEBOOK_APP_ID
        self.app_secret = settings.FACEBOOK_APP_SECRET
        self.api_version = settings.FACEBOOK_API_VERSION
        self.redirect_uri = settings.FACEBOOK_REDIRECT_URI
        self.default_scopes = [
            "public_profile",
            "pages_show_list",
            "pages_read_engagement",
            "ads_read",
        ]
        self.redis = None

    async def initialize(self):
        """Khởi tạo service và các kết nối cần thiết"""
        await self._init_redis()
        return self

    async def _init_redis(self):
        """Khởi tạo kết nối Redis"""
        try:
            self.redis = redis_asyncio.from_url(settings.REDIS_URL)
            logging.info("Connected to Redis for token storage")
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {str(e)}")
            # Sử dụng fallback là memory storage
            self.redis = None

    def get_authorization_url(
        self, scopes: Optional[List[str]] = None, state: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Tạo URL cho OAuth authorization flow

        Args:
            scopes: Danh sách các permissions cần yêu cầu
            state: State parameter để bảo vệ CSRF

        Returns:
            Dict chứa authorization URL và state
        """
        if not scopes:
            scopes = self.default_scopes

        if not state:
            # Generate random state parameter
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": ",".join(scopes),
            "response_type": "code",
        }

        # Xây dựng URL với parameters
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"https://www.facebook.com/{self.api_version}/dialog/oauth?{query_string}"

        return {"authorization_url": auth_url, "state": state}

    async def exchange_code_for_token(self, code: str) -> FacebookUserToken:
        """
        Trao đổi authorization code để lấy access token

        Args:
            code: Authorization code từ OAuth redirect

        Returns:
            FacebookUserToken object chứa token details

        Raises:
            AuthError: Nếu exchange thất bại
        """
        try:

            # Kiểm tra kỹ lưỡng các giá trị cấu hình bắt buộc
            logging.info(
                f"Attempting to exchange code for token with app_id: {self.app_id}, redirect_uri: {self.redirect_uri}"
            )

            if not self.app_id:
                logging.error("FACEBOOK_APP_ID is missing in configuration")
                raise AuthError(
                    "Missing FACEBOOK_APP_ID configuration", "config_error"
                )

            if not self.app_secret:
                logging.error("FACEBOOK_APP_SECRET is missing in configuration")
                raise AuthError(
                    "Missing FACEBOOK_APP_SECRET configuration", "config_error"
                )

            if not self.redirect_uri:
                logging.error(
                    "FACEBOOK_REDIRECT_URI is missing in configuration"
                )
                raise AuthError(
                    "Missing FACEBOOK_REDIRECT_URI configuration",
                    "config_error",
                )

            # Khởi tạo API với app credentials
            try:

                api = FacebookAdsApi.init(
                    app_id=self.app_id,
                    app_secret=self.app_secret,
                    access_token=code,
                    api_version=self.api_version,
                )
            except Exception as api_init_error:
                logging.error(
                    f"Facebook CODE: {self.app_id}-{self.app_secret}-{self.api_version} "
                )

                logging.error(
                    f"Failed to initialize Facebook API: {str(api_init_error)}"
                )
                raise AuthError(
                    f"Failed to initialize Facebook API: {str(api_init_error)}",
                    "api_init_error",
                )

            # Exchange code để lấy token
            try:
                token_response = api.call(
                    method="GET",
                    path="https://graph.facebook.com/v22.0/oauth/access_token",
                    params={
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "redirect_uri": self.redirect_uri,
                        "code": code,
                    },
                )
            except Exception as api_call_error:
                logging.error(
                    f"Failed to exchange code for token: {str(api_call_error)}"
                )
                raise AuthError(
                    f"Failed to exchange code for token: {str(api_call_error)}",
                    "token_exchange_error",
                )

            # Lấy thông tin từ response
            token_data = token_response.json()
            if "access_token" in token_data:
                access_token = token_data["access_token"]
            else:
                raise Exception(
                    f"Failed to exchange code for token: {token_data}"
                )

            if not access_token:
                logging.error("No access token in response")
                raise AuthError(
                    "No access token in response", "token_exchange_error"
                )

            # Validate token và lấy thêm thông tin
            validation_response = await self.validate_token(access_token)
            if not validation_response.is_valid:
                raise AuthError(
                    f"Invalid token received: {validation_response.error_message}",
                    "invalid_token",
                )

            # Tạo token model
            user_token = FacebookUserToken(
                user_id=validation_response.user_id,
                access_token=access_token,
                expires_at=validation_response.expires_at,
                is_valid=True,
                scopes=validation_response.scopes,
            )

            # Lưu token vào storage
            await self._store_user_token(user_token)

            return user_token

        except FacebookRequestError as e:
            logging.error(f"Facebook API error during token exchange: {str(e)}")
            raise AuthError(
                f"Facebook API error: {e.api_error_message()}",
                f"facebook_error_{e.api_error_code()}",
            )
        except Exception as e:
            logging.error(f"Error during code exchange: {str(e)}")
            raise AuthError(f"Failed to exchange code for token: {str(e)}")

    async def validate_token(self, token: str) -> TokenValidationResponse:
        """
        Kiểm tra token có valid hay không

        Args:
            token: Facebook access token cần kiểm tra

        Returns:
            TokenValidationResponse với thông tin validation
        """
        try:
            # Kiểm tra các giá trị cấu hình bắt buộc
            if not self.app_id or not self.app_secret:
                return TokenValidationResponse(
                    is_valid=False,
                    app_id=self.app_id or "",
                    application="",
                    error_message="Missing required configuration (app_id or app_secret)",
                )

            # Khởi tạo API
            api = FacebookAdsApi.init(
                app_id=self.app_id,
                app_secret=self.app_secret,
                api_version=self.api_version,
                access_token=token,
            )

            # Debug token
            # Debug token bằng cách gọi endpoint /debug_token
            debug_response = api.call(
                method="GET",
                path=f"https://graph.facebook.com/{self.api_version}/debug_token",  # URL đầy đủ
                params={
                    "input_token": token,  # Token cần kiểm tra
                    "access_token": f"{self.app_id}|{self.app_secret}",  # App token để xác thực yêu cầu
                },
            )

            # Lấy thông tin debug
            debug_info = debug_response.json()

            # Parse response
            expires_at = None
            if (
                "data_access_expires_at" in debug_info["data"]
                and debug_info["data"]["data_access_expires_at"]
            ):
                expires_at = datetime.fromtimestamp(
                    debug_info["data"]["data_access_expires_at"]
                )

            return TokenValidationResponse(
                is_valid=debug_info["data"].get("is_valid", False),
                app_id=debug_info["data"].get("app_id", self.app_id),
                application=debug_info["data"].get("application", ""),
                user_id=debug_info["data"].get("user_id"),
                scopes=debug_info["data"].get("scopes", []),
                expires_at=expires_at,
            )
        except FacebookRequestError as e:
            logging.error(
                f"Facebook API error during token validation: {str(e)}"
            )
            return TokenValidationResponse(
                is_valid=False,
                app_id=self.app_id,
                application="",
                error_message=f"Facebook API error: {e.api_error_message()}",
            )
        except Exception as e:
            logging.error(f"Error validating token: {str(e)}")
            return TokenValidationResponse(
                is_valid=False,
                app_id=self.app_id,
                application="",
                error_message=f"Error validating token: {str(e)}",
            )

    async def get_user_pages(self, user_token: str) -> List[FacebookPageToken]:
        """
        Lấy danh sách pages mà user có quyền truy cập

        Args:
            user_token: Access token của user

        Returns:
            List các FacebookPageToken

        Raises:
            AuthError: Nếu có lỗi khi lấy page tokens
        """
        try:
            # Khởi tạo API với user token
            api = FacebookAdsApi.init(
                app_id=self.app_id,
                app_secret=self.app_secret,
                access_token=user_token,
                api_version=self.api_version,
            )

            # Lấy thông tin user
            validation = await self.validate_token(user_token)
            if not validation.is_valid:
                raise AuthError("Invalid user token", "invalid_token")

            user_id = validation.user_id
            if not user_id:
                raise AuthError("Could not determine user ID", "unknown_user")

            # Lấy danh sách pages
            user = User(user_id)
            accounts = user.get_accounts(
                fields=["id", "name", "access_token", "category"]
            )

            # Tạo và lưu page tokens
            page_tokens = []
            for account in accounts:
                page_token = FacebookPageToken(
                    user_id=user_id,
                    page_id=account["id"],
                    page_name=account["name"],
                    access_token=account["access_token"],
                    category=account.get("category"),
                )

                # Lưu page token
                await self._store_page_token(page_token)
                page_tokens.append(page_token)

            return page_tokens

        except FacebookRequestError as e:
            logging.error(
                f"Facebook API error while getting user pages: {str(e)}"
            )
            raise AuthError(
                f"Facebook API error: {e.api_error_message()}",
                f"facebook_error_{e.api_error_code()}",
            )
        except Exception as e:
            logging.error(f"Error getting user pages: {str(e)}")
            raise AuthError(f"Failed to get user pages: {str(e)}")

    async def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh token khi sắp hết hạn

        Args:
            token: Token cần refresh

        Returns:
            New access token hoặc None nếu không thể refresh
        """
        try:
            # Kiểm tra các giá trị cấu hình bắt buộc
            if not self.app_id or not self.app_secret:
                logging.error(
                    "Missing required configuration (app_id or app_secret)"
                )
                return None

            # Lưu ý: Long-lived page tokens không cần refresh
            # Facebook API hiện cung cấp long-lived user tokens (60 ngày)
            # Cần validate token trước
            validation = await self.validate_token(token)

            # Nếu token không valid hoặc không có thông tin expires
            if not validation.is_valid:
                logging.warning(
                    f"Cannot refresh invalid token: {validation.error_message}"
                )
                return None

            # Kiểm tra expires_at
            if (
                not validation.expires_at
                or validation.expires_at > datetime.now() + timedelta(days=3)
            ):
                # Token còn hạn dài (>3 ngày) hoặc không có expiration
                logging.info("Token does not need refresh yet")
                return token

            # Khởi tạo API với app credential để refresh token
            api = FacebookAdsApi.init(
                app_id=self.app_id,
                app_secret=self.app_secret,
                api_version=self.api_version,
                access_token=token,
            )

            # Exchange code để lấy token
            try:
                token_response = api.call(
                    method="GET",
                    path="https://graph.facebook.com/v22.0/oauth/access_token",
                    params={
                        "grant_type": "fb_exchange_token",
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "fb_exchange_token": token,
                    },
                )
            except Exception as api_call_error:
                logging.error(
                    f"Failed to exchange code for token: {str(api_call_error)}"
                )
                raise AuthError(
                    f"Failed to exchange code for token: {str(api_call_error)}",
                    "token_exchange_error",
                )

            # Lấy thông tin từ response
            token_data = token_response.json()
            if "access_token" in token_data:
                new_token = token_data["access_token"]
            else:
                raise Exception(
                    f"Failed to exchange code for token: {token_data}"
                )

            if not new_token:
                logging.error("No access token in response")
                raise AuthError(
                    "No access token in response", "token_exchange_error"
                )

            # Update token trong storage
            user_id = validation.user_id
            if user_id:
                # Lấy token cũ
                old_token_data = await self._get_user_token(user_id)
                if old_token_data:
                    # Tạo token model mới
                    new_validation = await self.validate_token(new_token)
                    user_token = FacebookUserToken(
                        user_id=user_id,
                        access_token=new_token,
                        token_type="user",
                        expires_at=new_validation.expires_at,
                        is_valid=new_validation.is_valid,
                        scopes=new_validation.scopes,
                        updated_at=datetime.now(),
                    )
                    # Lưu vào storage
                    await self._store_user_token(user_token)

            return new_token

        except FacebookRequestError as e:
            logging.error(f"Facebook API error refreshing token: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error refreshing token: {str(e)}")
            return None

    async def get_token_by_user_id(
        self, user_id: str
    ) -> Optional[FacebookUserToken]:
        """
        Lấy token từ storage bằng user ID

        Args:
            user_id: Facebook user ID

        Returns:
            FacebookUserToken hoặc None nếu không tìm thấy
        """
        return await self._get_user_token(user_id)

    async def get_page_token(self, page_id: str) -> Optional[FacebookPageToken]:
        """
        Lấy page token từ storage bằng page ID

        Args:
            page_id: Facebook page ID

        Returns:
            FacebookPageToken hoặc None nếu không tìm thấy
        """
        return await self._get_page_token(page_id)

    # Helper methods for token storage

    async def _store_user_token(self, token: FacebookUserToken) -> None:
        """Lưu user token vào storage"""
        if not self.redis:
            logging.warning("Redis not available, token will not be persisted")
            return

        try:
            key = f"facebook:user_token:{token.user_id}"
            await self.redis.set(key, token.json())
            # Set expiration time nếu token có
            if token.expires_at:
                ttl = int((token.expires_at - datetime.now()).total_seconds())
                if ttl > 0:
                    await self.redis.expire(
                        key, ttl + 86400
                    )  # Thêm 1 ngày buffer
        except Exception as e:
            logging.error(f"Error storing user token: {str(e)}")

    async def _store_page_token(self, token: FacebookPageToken) -> None:
        """Lưu page token vào storage"""
        if not self.redis:
            logging.warning("Redis not available, token will not be persisted")
            return

        try:
            # Lưu theo page ID
            page_key = f"facebook:page_token:{token.page_id}"
            await self.redis.set(page_key, token.json())

            # Lưu vào list pages của user
            user_pages_key = f"facebook:user_pages:{token.user_id}"
            await self.redis.sadd(user_pages_key, token.page_id)
        except Exception as e:
            logging.error(f"Error storing page token: {str(e)}")

    async def _get_user_token(
        self, user_id: str
    ) -> Optional[FacebookUserToken]:
        """Lấy user token từ storage"""
        if not self.redis:
            logging.warning("Redis not available, cannot retrieve token")
            return None

        try:
            key = f"facebook:user_token:{user_id}"
            data = await self.redis.get(key)
            if not data:
                return None

            return FacebookUserToken.parse_raw(data)
        except Exception as e:
            logging.error(f"Error retrieving user token: {str(e)}")
            return None

    async def _get_page_token(
        self, page_id: str
    ) -> Optional[FacebookPageToken]:
        """Lấy page token từ storage"""
        if not self.redis:
            logging.warning("Redis not available, cannot retrieve token")
            return None

        try:
            key = f"facebook:page_token:{page_id}"
            data = await self.redis.get(key)
            if not data:
                return None

            return FacebookPageToken.parse_raw(data)
        except Exception as e:
            logging.error(f"Error retrieving page token: {str(e)}")
            return None
