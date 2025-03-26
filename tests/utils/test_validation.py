"""Tests cho validation utilities."""

import unittest
from datetime import datetime, timedelta

from app.models.core import DateRange, MetricsFilter
from app.utils.errors import ValidationError
from app.utils.validation import (
    validate_api_key,
    validate_date_range,
    validate_dimensions,
    validate_metrics,
    validate_metrics_filter,
    validate_pagination_params,
    validate_sort_params,
)


class TestValidationUtils(unittest.TestCase):
    """Test cases cho validation utils."""

    def test_validate_date_range_valid(self):
        """Test validate_date_range với valid range."""
        now = datetime.now()
        start_date = now - timedelta(days=30)
        end_date = now - timedelta(days=1)

        date_range = DateRange(start_date=start_date, end_date=end_date)

        # Should not raise exception
        validate_date_range(date_range)

    def test_validate_date_range_future_start(self):
        """Test validate_date_range với future start date."""
        now = datetime.now()
        start_date = now + timedelta(days=1)
        end_date = now + timedelta(days=30)

        date_range = DateRange(start_date=start_date, end_date=end_date)

        with self.assertRaises(ValidationError) as context:
            validate_date_range(date_range)

        self.assertIn(
            "Start date cannot be in the future", str(context.exception)
        )

    def test_validate_date_range_start_after_end(self):
        """Test validate_date_range với start date sau end date."""
        now = datetime.now()
        start_date = now - timedelta(days=10)
        end_date = now - timedelta(days=30)

        date_range = DateRange(start_date=start_date, end_date=end_date)

        with self.assertRaises(ValidationError) as context:
            validate_date_range(date_range)

        self.assertIn(
            "Start date must be before end date", str(context.exception)
        )

    def test_validate_date_range_too_long(self):
        """Test validate_date_range với range quá dài."""
        now = datetime.now()
        start_date = now - timedelta(days=400)
        end_date = now - timedelta(days=1)

        date_range = DateRange(start_date=start_date, end_date=end_date)

        with self.assertRaises(ValidationError) as context:
            validate_date_range(date_range)

        self.assertIn("Date range too large", str(context.exception))

    def test_validate_metrics_valid(self):
        """Test validate_metrics với valid metrics."""
        metrics = ["impressions", "clicks", "ctr"]
        allowed_metrics = ["impressions", "clicks", "ctr", "spend"]

        # Should not raise exception
        validate_metrics(metrics, allowed_metrics)

    def test_validate_metrics_invalid(self):
        """Test validate_metrics với invalid metrics."""
        metrics = ["impressions", "invalid_metric", "clicks"]
        allowed_metrics = ["impressions", "clicks", "ctr", "spend"]

        with self.assertRaises(ValidationError) as context:
            validate_metrics(metrics, allowed_metrics)

        self.assertIn("Invalid metrics specified", str(context.exception))
        self.assertIn("invalid_metric", str(context.exception))

    def test_validate_dimensions_valid(self):
        """Test validate_dimensions với valid dimensions."""
        dimensions = ["date", "campaign"]
        allowed_dimensions = ["date", "campaign", "ad_group"]

        # Should not raise exception
        validate_dimensions(dimensions, allowed_dimensions)

    def test_validate_dimensions_invalid(self):
        """Test validate_dimensions với invalid dimensions."""
        dimensions = ["date", "invalid_dim"]
        allowed_dimensions = ["date", "campaign", "ad_group"]

        with self.assertRaises(ValidationError) as context:
            validate_dimensions(dimensions, allowed_dimensions)

        self.assertIn("Invalid dimensions specified", str(context.exception))
        self.assertIn("invalid_dim", str(context.exception))

    def test_validate_metrics_filter_valid(self):
        """Test validate_metrics_filter với valid filter."""
        now = datetime.now()
        start_date = now - timedelta(days=30)
        end_date = now - timedelta(days=1)

        date_range = DateRange(start_date=start_date, end_date=end_date)
        metrics = ["impressions", "clicks"]
        dimensions = ["date"]

        metrics_filter = MetricsFilter(
            date_range=date_range, metrics=metrics, dimensions=dimensions
        )

        allowed_metrics = ["impressions", "clicks", "ctr", "spend"]
        allowed_dimensions = ["date", "campaign", "ad_group"]

        # Should not raise exception
        validate_metrics_filter(
            metrics_filter, allowed_metrics, allowed_dimensions
        )

    def test_validate_metrics_filter_invalid(self):
        """Test validate_metrics_filter với invalid filter."""
        now = datetime.now()
        start_date = now - timedelta(days=30)
        end_date = now - timedelta(days=1)

        date_range = DateRange(start_date=start_date, end_date=end_date)
        metrics = ["impressions", "invalid_metric"]
        dimensions = ["date"]

        metrics_filter = MetricsFilter(
            date_range=date_range, metrics=metrics, dimensions=dimensions
        )

        allowed_metrics = ["impressions", "clicks", "ctr", "spend"]
        allowed_dimensions = ["date", "campaign", "ad_group"]

        with self.assertRaises(ValidationError) as context:
            validate_metrics_filter(
                metrics_filter, allowed_metrics, allowed_dimensions
            )

        self.assertIn("Invalid metrics specified", str(context.exception))

    def test_validate_api_key_valid(self):
        """Test validate_api_key với valid API key."""
        valid_keys = [
            "valid-api-key-12345",
            "abcdef1234567890",
            "test_key_12345_abcde",
        ]

        for key in valid_keys:
            self.assertTrue(validate_api_key(key))

    def test_validate_api_key_invalid(self):
        """Test validate_api_key với invalid API key."""
        invalid_keys = [
            "",  # Empty
            "short",  # Too short
            "invalid@key",  # Invalid character
            "   spaces   ",  # Spaces
        ]

        for key in invalid_keys:
            self.assertFalse(validate_api_key(key))

    def test_validate_pagination_params_valid(self):
        """Test validate_pagination_params với valid params."""
        # Normal case
        page, page_size = validate_pagination_params(1, 20)
        self.assertEqual(page, 1)
        self.assertEqual(page_size, 20)

        # Edge case
        page, page_size = validate_pagination_params(100, 50)
        self.assertEqual(page, 100)
        self.assertEqual(page_size, 50)

    def test_validate_pagination_params_invalid(self):
        """Test validate_pagination_params với invalid params."""
        # Invalid page
        with self.assertRaises(ValidationError) as context:
            validate_pagination_params(0, 20)
        self.assertIn("Page number must be at least 1", str(context.exception))

        # Invalid page_size (too small)
        with self.assertRaises(ValidationError) as context:
            validate_pagination_params(1, 0)
        self.assertIn("Page size must be at least 1", str(context.exception))

        # Invalid page_size (too large)
        with self.assertRaises(ValidationError) as context:
            validate_pagination_params(1, 200, max_page_size=100)
        self.assertIn(
            "Page size exceeds maximum allowed value", str(context.exception)
        )

    def test_validate_sort_params_valid(self):
        """Test validate_sort_params với valid params."""
        allowed_fields = ["date", "impressions", "clicks"]

        # Normal case
        sort_by, sort_order = validate_sort_params(
            "date", "asc", allowed_fields
        )
        self.assertEqual(sort_by, "date")
        self.assertEqual(sort_order, "asc")

        # Case insensitive sort order
        sort_by, sort_order = validate_sort_params(
            "impressions", "DESC", allowed_fields
        )
        self.assertEqual(sort_by, "impressions")
        self.assertEqual(sort_order, "desc")

    def test_validate_sort_params_invalid(self):
        """Test validate_sort_params với invalid params."""
        allowed_fields = ["date", "impressions", "clicks"]

        # Invalid sort_by
        with self.assertRaises(ValidationError) as context:
            validate_sort_params("invalid_field", "asc", allowed_fields)
        self.assertIn("Invalid sort field", str(context.exception))

        # Invalid sort_order
        with self.assertRaises(ValidationError) as context:
            validate_sort_params("date", "random", allowed_fields)
        self.assertIn("Invalid sort order", str(context.exception))


if __name__ == "__main__":
    unittest.main()
