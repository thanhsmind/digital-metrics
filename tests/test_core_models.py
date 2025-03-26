from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
from pydantic import ValidationError

from app.models.core import (
    BaseResponse,
    DateRange,
    MetricsFilter,
    MetricsResponse,
    PaginatedResponse,
    PaginationParams,
)


class TestDateRange:
    def test_valid_date_range(self):
        """Test DateRange với ngày hợp lệ."""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        date_range = DateRange(start_date=start_date, end_date=end_date)

        assert date_range.start_date == start_date
        assert date_range.end_date == end_date

    def test_invalid_date_range(self):
        """Test DateRange với end_date trước start_date."""
        end_date = datetime.now() - timedelta(days=7)
        start_date = datetime.now()

        with pytest.raises(ValidationError) as exc_info:
            DateRange(start_date=start_date, end_date=end_date)

        assert "end_date phải sau start_date" in str(exc_info.value)


class TestMetricsFilter:
    def test_metrics_filter_with_dimensions(self):
        """Test MetricsFilter với dimensions."""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        metrics_filter = MetricsFilter(
            date_range=DateRange(start_date=start_date, end_date=end_date),
            metrics=["impressions", "clicks", "ctr"],
            dimensions=["campaign", "date"],
        )

        assert metrics_filter.metrics == ["impressions", "clicks", "ctr"]
        assert metrics_filter.dimensions == ["campaign", "date"]

    def test_metrics_filter_without_dimensions(self):
        """Test MetricsFilter không có dimensions."""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        metrics_filter = MetricsFilter(
            date_range=DateRange(start_date=start_date, end_date=end_date),
            metrics=["impressions", "clicks", "ctr"],
        )

        assert metrics_filter.metrics == ["impressions", "clicks", "ctr"]
        assert metrics_filter.dimensions is None


class TestPaginationParams:
    def test_default_pagination(self):
        """Test PaginationParams với giá trị mặc định."""
        params = PaginationParams()

        assert params.page == 1
        assert params.page_size == 20

    def test_custom_pagination(self):
        """Test PaginationParams với giá trị tùy chỉnh."""
        params = PaginationParams(page=2, page_size=50)

        assert params.page == 2
        assert params.page_size == 50

    def test_invalid_pagination(self):
        """Test PaginationParams với giá trị không hợp lệ."""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)


class TestResponseModels:
    def test_base_response(self):
        """Test BaseResponse."""
        response = BaseResponse()
        assert response.success is True
        assert response.message is None

        response = BaseResponse(message="Thành công")
        assert response.success is True
        assert response.message == "Thành công"

        response = BaseResponse(success=False, message="Lỗi")
        assert response.success is False
        assert response.message == "Lỗi"

    def test_paginated_response(self):
        """Test PaginatedResponse."""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]

        response = PaginatedResponse(
            total=100, page=2, page_size=3, total_pages=34, data=data
        )

        assert response.success is True
        assert response.total == 100
        assert response.page == 2
        assert response.page_size == 3
        assert response.total_pages == 34
        assert response.data == data

    def test_metrics_response(self):
        """Test MetricsResponse."""
        data = [
            {"date": "2023-01-01", "impressions": 1000, "clicks": 100},
            {"date": "2023-01-02", "impressions": 1200, "clicks": 120},
        ]

        summary = {"impressions": 2200, "clicks": 220}

        response = MetricsResponse(data=data, summary=summary)

        assert response.success is True
        assert response.data == data
        assert response.summary == summary
