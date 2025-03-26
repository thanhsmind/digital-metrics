import json
import logging
import os
from datetime import datetime
from typing import Dict, Optional

from app.core.config import settings
from app.services.facebook.auth_service import FacebookAuthService


class TokenManager:
    """Quản lý lưu trữ token và cập nhật tự động"""

    def __init__(self):
        self.auth_service = FacebookAuthService()
        self.token_file = "facebook_tokens.json"

    async def load_token(self) -> Optional[str]:
        """Tải token từ file hoặc từ settings"""
        # Kiểm tra FACEBOOK_APP_ID và FACEBOOK_APP_SECRET đã được thiết lập chưa
        if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
            logging.warning(
                "FACEBOOK_APP_ID hoặc FACEBOOK_APP_SECRET chưa được cấu hình"
            )
            return None

        # Ưu tiên dùng token từ settings
        if settings.FACEBOOK_ACCESS_TOKEN:
            logging.info("Using access token from environment settings")
            return settings.FACEBOOK_ACCESS_TOKEN

        # Nếu không có, thử đọc từ file
        try:
            if os.path.exists(self.token_file):
                logging.info(
                    f"Token file found at {self.token_file}, loading token"
                )
                with open(self.token_file, "r") as f:
                    data = json.load(f)
                    if "access_token" in data:
                        return data["access_token"]
                    else:
                        logging.warning(
                            "Token file exists but does not contain access_token field"
                        )
            else:
                logging.warning(f"Token file {self.token_file} does not exist")
        except Exception as e:
            logging.error(f"Error loading token from file: {str(e)}")

        logging.warning("No token available from environment or file")
        return None

    async def save_token(self, token: str, token_data: Dict = None):
        """Lưu token vào file"""
        try:
            data = {
                "access_token": token,
                "updated_at": datetime.now().isoformat(),
            }

            # Thêm metadata nếu có
            if token_data:
                data.update(token_data)

            with open(self.token_file, "w") as f:
                json.dump(data, f, indent=2)

            logging.info(f"Token saved to {self.token_file}")
        except Exception as e:
            logging.error(f"Error saving token to file: {str(e)}")

    async def refresh_token_if_needed(self) -> Optional[str]:
        """Kiểm tra và làm mới token nếu cần"""
        current_token = await self.load_token()
        if not current_token:
            logging.warning("No token available to refresh")
            return None

        # Validate token
        validation = await self.auth_service.validate_token(current_token)

        # Nếu token hợp lệ thì trả về token hiện tại
        if validation.is_valid and (
            not validation.expires_at
            or (
                validation.expires_at and validation.expires_at > datetime.now()
            )
        ):
            return current_token

        # Nếu token không hợp lệ hoặc hết hạn, thử refresh
        new_token = await self.auth_service.refresh_token(current_token)
        if new_token:
            # Validate token mới
            new_validation = await self.auth_service.validate_token(new_token)

            # Lưu token mới
            await self.save_token(
                new_token,
                {
                    "expires_at": (
                        new_validation.expires_at.isoformat()
                        if new_validation.expires_at
                        else None
                    ),
                    "user_id": new_validation.user_id,
                    "scopes": new_validation.scopes,
                },
            )

            # Cập nhật settings runtime
            settings.FACEBOOK_ACCESS_TOKEN = new_token

            return new_token

        return None

    async def get_or_create_token(self) -> Optional[str]:
        """Lấy token hiện tại hoặc tạo mới nếu cần"""
        # Thử lấy token hiện tại
        token = await self.load_token()

        # Nếu có token, kiểm tra và làm mới nếu cần
        if token:
            return await self.refresh_token_if_needed()

        # Nếu không có token, cần flow OAuth mới
        logging.warning("No token available, need to complete OAuth flow")
        return None

    async def refresh_all_tokens(self) -> bool:
        """
        Làm mới tất cả các token đã lưu trữ

        Returns:
            bool: True nếu ít nhất một token được làm mới thành công, False nếu không
        """
        logging.info("Starting refresh of all stored tokens")
        success = False

        # Làm mới token chính (từ settings hoặc file)
        current_token = await self.load_token()
        if current_token:
            logging.info("Refreshing main access token")
            new_token = await self.refresh_token_if_needed()
            if new_token:
                success = True
                logging.info("Main token refreshed successfully")
            else:
                logging.warning("Failed to refresh main token")
        else:
            logging.warning("No main token found to refresh")

        # TODO: Nếu có lưu trữ nhiều token (ví dụ: Redis), có thể làm mới tất cả ở đây

        return success
