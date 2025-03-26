import logging
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.services.facebook.auth_service import FacebookAuthService


class TokenRefreshMiddleware(BaseHTTPMiddleware):
    """Middleware để tự động kiểm tra và làm mới Facebook access token"""

    def __init__(self, app):
        super().__init__(app)
        self.auth_service = FacebookAuthService()
        self.last_checked = datetime.now()
        self.check_interval = timedelta(hours=1)  # Kiểm tra 1 lần mỗi giờ

    async def dispatch(self, request: Request, call_next):
        # Chỉ kiểm tra token trên các endpoint Facebook
        if (
            "/api/v1/facebook/" in request.url.path
            and self._should_check_token()
        ):
            await self._check_and_refresh_token()

        # Tiếp tục request chain
        response = await call_next(request)
        return response

    def _should_check_token(self) -> bool:
        """Kiểm tra xem đã đến lúc check token chưa"""
        now = datetime.now()
        if now - self.last_checked > self.check_interval:
            self.last_checked = now
            return True
        return False

    async def _check_and_refresh_token(self):
        """Kiểm tra và làm mới token nếu cần"""
        try:
            token = settings.FACEBOOK_ACCESS_TOKEN
            if not token:
                logging.warning("No Facebook access token configured")
                return

            # Validate token
            validation = await self.auth_service.validate_token(token)

            # Nếu token không hợp lệ hoặc sắp hết hạn (còn dưới 7 ngày)
            if not validation.is_valid or (
                validation.expires_at
                and validation.expires_at < datetime.now() + timedelta(days=7)
            ):
                logging.info(
                    "Token is invalid or expiring soon, attempting to refresh"
                )
                new_token = await self.auth_service.refresh_token(token)

                if new_token:
                    # Cập nhật token vào settings runtime
                    settings.FACEBOOK_ACCESS_TOKEN = new_token
                    logging.info("Facebook access token refreshed successfully")

                    # Cập nhật token trong FacebookApiManager
                    # Chú ý: Cần thêm method vào FacebookApiManager để cập nhật token
                    from app.services.facebook.api import FacebookApiManager

                    api_manager = FacebookApiManager()
                    api_manager.update_access_token(new_token)
                else:
                    logging.error("Failed to refresh Facebook access token")
        except Exception as e:
            logging.error(f"Error in token refresh middleware: {str(e)}")
