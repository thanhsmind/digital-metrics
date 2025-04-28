import logging
from typing import Callable, Dict, Optional

from facebook_business.exceptions import FacebookRequestError
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.services.facebook.token_manager import TokenManager


class TokenMiddleware(BaseHTTPMiddleware):
    """Middleware xử lý token hết hạn tự động"""

    def __init__(self, app):
        super().__init__(app)
        self.token_manager = TokenManager()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle token expiry during request processing.

        If a FacebookRequestError is raised with an expired token error,
        attempt to refresh the token and retry the request if needed.
        """
        # Lưu trữ token cũ (nếu có) để có thể so sánh và cập nhật sau này
        old_token = self._extract_token_from_request(request)

        try:
            # Thử thực hiện request
            response = await call_next(request)
            return response

        except FacebookRequestError as e:
            # Kiểm tra xem có phải lỗi token hết hạn không
            if self._is_token_expired_error(e) and old_token:
                logging.warning(
                    f"Token expired error detected: {e.api_error_message()}"
                )

                try:
                    # Thử làm mới token
                    new_token = (
                        await self.token_manager.refresh_token_on_demand(
                            old_token
                        )
                    )

                    if new_token and new_token != old_token:
                        logging.info(
                            "Token refreshed successfully, retrying request"
                        )

                        # Tạo request mới với token đã được làm mới
                        new_request = await self._create_new_request_with_token(
                            request, new_token
                        )

                        # Thử lại request với token mới
                        return await call_next(new_request)
                    else:
                        logging.error(
                            "Failed to refresh token or token unchanged"
                        )

                except Exception as refresh_error:
                    logging.error(
                        f"Error refreshing token: {str(refresh_error)}"
                    )

            # Nếu không phải lỗi token hết hạn hoặc không thể làm mới token, throw lại lỗi ban đầu
            logging.error(f"Facebook API error: {e.api_error_message()}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Facebook API error: {e.api_error_message()}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        except Exception as e:
            # Xử lý các lỗi khác
            logging.error(f"Error in request processing: {str(e)}")
            raise

    def _is_token_expired_error(self, error: FacebookRequestError) -> bool:
        """
        Kiểm tra xem lỗi có phải là do token hết hạn không

        Args:
            error: FacebookRequestError object

        Returns:
            True nếu là lỗi token hết hạn, False nếu không
        """
        # Mã lỗi thường gặp khi token hết hạn
        token_expired_codes = [190, 102, 4, 2500]

        # Check error code
        if (
            hasattr(error, "api_error_code")
            and error.api_error_code() in token_expired_codes
        ):
            return True

        # Check error message
        if hasattr(error, "api_error_message"):
            message = error.api_error_message().lower()
            expired_keywords = [
                "expired",
                "invalid token",
                "access token",
                "oauth",
                "permission",
            ]
            return any(keyword in message for keyword in expired_keywords)

        return False

    def _extract_token_from_request(self, request: Request) -> Optional[str]:
        """
        Lấy token từ request

        Args:
            request: Request object

        Returns:
            Token string hoặc None nếu không tìm thấy
        """
        # Thử lấy từ Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.replace("Bearer ", "")

        # Thử lấy từ query parameters
        token = request.query_params.get("access_token")
        if token:
            return token

        # Nếu không tìm thấy, dùng token mặc định từ settings
        return settings.FACEBOOK_ACCESS_TOKEN

    async def _create_new_request_with_token(
        self, original_request: Request, new_token: str
    ) -> Request:
        """
        Tạo request mới với token mới

        Args:
            original_request: Request object gốc
            new_token: Token mới

        Returns:
            Request object mới với token đã được cập nhật
        """
        # Lưu ý: Request object trong FastAPI là immutable
        # Nên chúng ta cần tạo một wrapper để ghi đè các thông tin cần thiết

        class RequestWrapper:
            def __init__(self, original_request: Request, new_token: str):
                self._request = original_request
                self._new_token = new_token

            async def __getattr__(self, name):
                return getattr(self._request, name)

            @property
            def headers(self) -> Dict:
                # Tạo headers mới với token đã cập nhật
                headers = dict(self._request.headers)
                headers["Authorization"] = f"Bearer {self._new_token}"
                return headers

            @property
            def query_params(self) -> Dict:
                # Tạo query params mới với token đã cập nhật nếu có token trong query
                params = dict(self._request.query_params)
                if "access_token" in params:
                    params["access_token"] = self._new_token
                return params

        return RequestWrapper(original_request, new_token)
