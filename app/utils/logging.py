"""Logging utilities cho Digital Metrics API."""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional, Union

from fastapi import FastAPI
from pythonjsonlogger import jsonlogger

# Constants
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_JSON_FORMAT = "%(timestamp)s %(level)s %(name)s %(message)s"


# Custom Logger setup
class APILogger:
    """
    Custom logger class dành riêng cho Digital Metrics API.
    Hỗ trợ cả standard log format và JSON format.
    """

    def __init__(
        self,
        name: str,
        log_level: int = logging.INFO,
        use_json: bool = False,
        log_to_file: bool = False,
        log_file_path: Optional[Union[str, Path]] = None,
    ):
        """
        Khởi tạo logger instance.

        Args:
            name: Tên của logger
            log_level: Logging level (mặc định là INFO)
            use_json: Có sử dụng JSON format không
            log_to_file: Có ghi log vào file không
            log_file_path: Path của log file nếu log_to_file=True
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.handlers = []  # Clear existing handlers

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)

        if use_json:
            formatter = self._create_json_formatter()
        else:
            formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler (if requested)
        if log_to_file:
            if not log_file_path:
                log_dir = Path("logs")
                log_dir.mkdir(exist_ok=True)
                log_file_path = log_dir / f"{name}.log"

            file_handler = RotatingFileHandler(
                log_file_path, maxBytes=10485760, backupCount=5
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _create_json_formatter(self) -> jsonlogger.JsonFormatter:
        """
        Tạo JSON formatter cho logging.

        Returns:
            JSON formatter instance
        """
        return jsonlogger.JsonFormatter(
            DEFAULT_JSON_FORMAT,
            rename_fields={"levelname": "level", "asctime": "timestamp"},
            json_default=lambda o: (
                f"{o}" if isinstance(o, datetime) else str(o)
            ),
        )

    # Forward tất cả log methods tới underlying logger
    def debug(self, msg: str, **kwargs):
        """Log debug message."""
        self.logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs):
        """Log info message."""
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg: str, **kwargs):
        """Log warning message."""
        self.logger.warning(msg, extra=kwargs)

    def error(self, msg: str, **kwargs):
        """Log error message."""
        self.logger.error(msg, extra=kwargs)

    def critical(self, msg: str, **kwargs):
        """Log critical message."""
        self.logger.critical(msg, extra=kwargs)

    def exception(self, msg: str, **kwargs):
        """Log exception với traceback."""
        self.logger.exception(msg, extra=kwargs)


# Middleware
class RequestLoggingMiddleware:
    """
    Middleware để log request/response details.
    """

    def __init__(self, logger: APILogger):
        """
        Khởi tạo middleware với logger.

        Args:
            logger: APILogger instance
        """
        self.logger = logger

    async def __call__(self, request, call_next):
        """
        Process request, log details, và forward tới next middleware.

        Args:
            request: FastAPI request
            call_next: Next middleware function

        Returns:
            Response từ call_next
        """
        start_time = datetime.now()

        # Log request
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None,
        )

        # Process request
        try:
            response = await call_next(request)

            # Log response
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.info(
                f"Request completed: {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration, 2),
            )

            return response
        except Exception as e:
            # Log exception
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration, 2),
            )
            raise


# Helper functions
def setup_app_logging(app: FastAPI, config: Dict) -> APILogger:
    """
    Set up logging cho FastAPI application.

    Args:
        app: FastAPI application
        config: Dict với các logging config options

    Returns:
        Configured APILogger instance

    Examples:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> config = {"log_level": "INFO", "use_json": True}
        >>> logger = setup_app_logging(app, config)
    """
    log_level = getattr(logging, config.get("log_level", "INFO"))
    use_json = config.get("use_json", False)
    log_to_file = config.get("log_to_file", False)
    log_file_path = config.get("log_file_path")

    # Create logger
    logger = APILogger(
        "digital_metrics",
        log_level=log_level,
        use_json=use_json,
        log_to_file=log_to_file,
        log_file_path=log_file_path,
    )

    # Add request logging middleware if enabled
    if config.get("log_requests", True):
        from starlette.middleware.base import BaseHTTPMiddleware

        app.add_middleware(
            BaseHTTPMiddleware,
            dispatch=RequestLoggingMiddleware(logger),
        )

    logger.info("Application logging configured", config=config)
    return logger


def get_logger(name: str) -> APILogger:
    """
    Get logger instance theo tên.

    Args:
        name: Tên của module hoặc component

    Returns:
        APILogger instance

    Examples:
        >>> logger = get_logger("api.campaigns")
        >>> logger.info("Processing campaign data")
    """
    return APILogger(name)
