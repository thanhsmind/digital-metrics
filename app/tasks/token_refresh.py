import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import BackgroundTasks

from app.core.config import settings
from app.services.facebook.api import FacebookApiManager
from app.services.facebook.token_manager import TokenManager


class TokenRefreshTask:
    """Task để tự động kiểm tra và làm mới token theo chu kỳ"""

    def __init__(self):
        self.token_manager = TokenManager()
        self.api_manager = FacebookApiManager()
        self.is_running = False
        self.refresh_interval_hours = 24  # Mặc định 24 giờ
        self.refresh_task = None

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
                await asyncio.sleep(
                    self.refresh_interval_hours * 60 * 60
                )  # Chuyển giờ thành giây

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

    async def schedule_periodic_refresh(self, hours: int = 24):
        """
        Thiết lập scheduled task để chạy refresh token định kỳ

        Args:
            hours: Số giờ giữa các lần refresh

        Returns:
            True nếu đã thiết lập thành công task, False nếu không
        """
        try:
            # Cập nhật refresh interval
            self.refresh_interval_hours = hours
            logging.info(f"Setting refresh interval to {hours} hours")

            # Nếu đã có task chạy, hủy task đó
            if self.refresh_task and not self.refresh_task.done():
                logging.info("Cancelling existing refresh task")
                self.refresh_task.cancel()

            # Tạo task mới
            self.refresh_task = asyncio.create_task(
                self.run_scheduled_refresh(hours)
            )
            logging.info(f"Scheduled token refresh every {hours} hours")
            return True
        except Exception as e:
            logging.error(f"Error scheduling periodic refresh: {str(e)}")
            return False

    async def run_scheduled_refresh(self, hours: int):
        """
        Chạy periodic refresh theo lịch đã định

        Args:
            hours: Số giờ giữa các lần refresh
        """
        try:
            while True:
                # Refresh các token sắp hết hạn trong 24 giờ tới
                logging.info(
                    f"Running scheduled token refresh at {datetime.now().isoformat()}"
                )
                results = await self.token_manager.refresh_expiring_tokens(24)

                # Log kết quả
                success_count = sum(
                    1 for r in results if r.get("success", False)
                )
                error_count = len(results) - success_count
                logging.info(
                    f"Scheduled refresh completed: {success_count} successes, {error_count} errors"
                )

                # Chờ đến lần refresh tiếp theo
                logging.info(f"Next scheduled refresh in {hours} hours")
                await asyncio.sleep(hours * 60 * 60)
        except asyncio.CancelledError:
            logging.info("Scheduled refresh task cancelled")
        except Exception as e:
            logging.error(f"Error in scheduled refresh task: {str(e)}")
            # Auto-restart sau lỗi, với delay để tránh vòng lặp lỗi
            logging.info("Restarting scheduled refresh after error")
            await asyncio.sleep(60)  # Đợi 1 phút trước khi thử lại
            await self.schedule_periodic_refresh(hours)

    async def refresh_all_tokens(self) -> Dict[str, Any]:
        """
        Refresh tất cả tokens trong hệ thống

        Returns:
            Dict với kết quả của quá trình refresh
        """
        logging.info("Starting token refresh task for all tokens")
        success = await self.token_manager.refresh_all_tokens()
        return {
            "success": success,
            "message": "Token refresh completed",
            "token_file": settings.FACEBOOK_TOKEN_FILE,
        }

    async def refresh_expiring_tokens(
        self, hours_threshold: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Refresh các token sắp hết hạn

        Args:
            hours_threshold: Số giờ trước khi token hết hạn cần refresh

        Returns:
            List các kết quả refresh
        """
        logging.info(
            f"Starting token refresh task for tokens expiring in {hours_threshold} hours"
        )
        results = await self.token_manager.refresh_expiring_tokens(
            hours_threshold
        )
        return results
