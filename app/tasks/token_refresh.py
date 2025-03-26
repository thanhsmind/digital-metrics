import asyncio
import logging
from datetime import datetime

from fastapi import BackgroundTasks

from app.services.facebook.api import FacebookApiManager
from app.services.facebook.token_manager import TokenManager


class TokenRefreshTask:
    """Task để tự động kiểm tra và làm mới token theo chu kỳ"""

    def __init__(self):
        self.token_manager = TokenManager()
        self.api_manager = FacebookApiManager()
        self.is_running = False

    async def start_background_task(self, background_tasks: BackgroundTasks):
        """Thêm nhiệm vụ làm mới token vào BackgroundTasks"""
        if not self.is_running:
            background_tasks.add_task(self.refresh_token_periodically)
            logging.info("Token refresh background task started")

    async def refresh_token_periodically(self):
        """Kiểm tra và làm mới token theo định kỳ"""
        self.is_running = True
        try:
            while True:
                logging.info(
                    f"Checking token status at {datetime.now().isoformat()}"
                )

                # Thực hiện kiểm tra token
                new_token = await self.token_manager.refresh_token_if_needed()

                if new_token:
                    # Cập nhật token cho API manager
                    self.api_manager.update_access_token(new_token)
                    logging.info("Token refreshed and updated in API manager")

                # Chờ 24 giờ trước khi kiểm tra lại
                # Có thể điều chỉnh theo nhu cầu
                await asyncio.sleep(24 * 60 * 60)  # 24 giờ

        except Exception as e:
            logging.error(f"Error in token refresh task: {str(e)}")
        finally:
            self.is_running = False

    async def refresh_token_now(self):
        """Thực hiện làm mới token ngay lập tức"""
        try:
            new_token = await self.token_manager.refresh_token_if_needed()
            if new_token:
                self.api_manager.update_access_token(new_token)
                logging.info("Token refreshed immediately")
                return True
            return False
        except Exception as e:
            logging.error(f"Error refreshing token: {str(e)}")
            return False
