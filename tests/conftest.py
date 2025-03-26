"""Pytest configuration cho Digital Metrics API tests."""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Generator, List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Đảm bảo "app" package có thể được import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.core import DateRange, MetricsFilter
from app.utils.caching import InMemoryCache
from app.utils.config import APIConfig, AppConfig, DatabaseConfig
from app.utils.errors import add_exception_handlers
from app.utils.logging import APILogger, get_logger


@pytest.fixture
def test_app() -> FastAPI:
    """
    Create FastAPI app instance cho testing.

    Returns:
        FastAPI app instance
    """
    app = FastAPI(title="Digital Metrics API", version="0.1.0")
    add_exception_handlers(app)
    return app


@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """
    Create FastAPI TestClient instance.

    Args:
        test_app: FastAPI app instance

    Returns:
        TestClient instance
    """
    return TestClient(test_app)


@pytest.fixture
def test_logger() -> APILogger:
    """
    Create test logger instance.

    Returns:
        APILogger instance
    """
    return get_logger("test")


@pytest.fixture
def test_cache() -> InMemoryCache:
    """
    Create test cache instance.

    Returns:
        InMemoryCache instance
    """
    return InMemoryCache()


@pytest.fixture
def test_config() -> AppConfig:
    """
    Create test config instance.

    Returns:
        AppConfig instance
    """
    return AppConfig(
        env="testing",
        debug=True,
        api=APIConfig(
            host="localhost", port=8000, debug=True, log_level="DEBUG"
        ),
        database=DatabaseConfig(
            host="localhost",
            port=5432,
            username="test_user",
            password="test_password",
            database="test_db",
        ),
    )


@pytest.fixture
def test_date_range() -> DateRange:
    """
    Create date range cho testing.

    Returns:
        DateRange instance
    """
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=30)
    return DateRange(start_date=start_date, end_date=end_date)


@pytest.fixture
def test_metrics_filter(test_date_range: DateRange) -> MetricsFilter:
    """
    Create metrics filter cho testing.

    Args:
        test_date_range: DateRange fixture

    Returns:
        MetricsFilter instance
    """
    return MetricsFilter(
        date_range=test_date_range,
        metrics=["impressions", "clicks", "ctr"],
        dimensions=["date", "campaign"],
    )


@pytest.fixture
def test_metrics_data() -> List[Dict]:
    """
    Create sample metrics data cho testing.

    Returns:
        List các metrics data points
    """
    return [
        {
            "date": "2023-01-01",
            "campaign": "Campaign 1",
            "impressions": 1234,
            "clicks": 123,
            "ctr": 0.0997,
        },
        {
            "date": "2023-01-02",
            "campaign": "Campaign 1",
            "impressions": 2345,
            "clicks": 234,
            "ctr": 0.0998,
        },
        {
            "date": "2023-01-01",
            "campaign": "Campaign 2",
            "impressions": 3456,
            "clicks": 345,
            "ctr": 0.0999,
        },
    ]
