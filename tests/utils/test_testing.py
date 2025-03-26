"""Tests cho testing utilities."""

import unittest
from datetime import datetime, timedelta

from app.models.core import DateRange
from app.utils.testing import (
    generate_date_range,
    generate_metrics_data,
    generate_metrics_filter,
    mock_facebook_campaign_response,
    mock_facebook_metrics_response,
    mock_google_campaign_response,
)


class TestTestingUtils(unittest.TestCase):
    """Test cases cho testing utilities."""

    def test_generate_date_range(self):
        """Test generate_date_range function."""
        # Test default values
        date_range = generate_date_range()
        self.assertIsInstance(date_range, DateRange)
        self.assertEqual((date_range.end_date - date_range.start_date).days, 30)

        # Test custom values
        date_range = generate_date_range(days_ago=7, days_range=7)
        self.assertEqual((date_range.end_date - date_range.start_date).days, 7)

        # Test time range is set to start of day
        now = datetime.now()
        self.assertEqual(date_range.end_date.hour, 0)
        self.assertEqual(date_range.end_date.minute, 0)
        self.assertEqual(date_range.end_date.second, 0)
        self.assertEqual(date_range.start_date.hour, 0)
        self.assertEqual(date_range.start_date.minute, 0)
        self.assertEqual(date_range.start_date.second, 0)

    def test_generate_metrics_filter(self):
        """Test generate_metrics_filter function."""
        # Test default values
        metrics_filter = generate_metrics_filter()
        self.assertIsInstance(metrics_filter.date_range, DateRange)
        self.assertEqual(
            metrics_filter.metrics, ["impressions", "clicks", "ctr", "spend"]
        )
        self.assertIsNone(metrics_filter.dimensions)

        # Test custom metrics
        custom_metrics = ["impressions", "clicks"]
        metrics_filter = generate_metrics_filter(metrics=custom_metrics)
        self.assertEqual(metrics_filter.metrics, custom_metrics)

        # Test custom dimensions
        custom_dimensions = ["date", "campaign"]
        metrics_filter = generate_metrics_filter(dimensions=custom_dimensions)
        self.assertEqual(metrics_filter.dimensions, custom_dimensions)

    def test_generate_metrics_data(self):
        """Test generate_metrics_data function."""
        # Setup
        date_range = DateRange(
            start_date=datetime(2023, 1, 1), end_date=datetime(2023, 1, 7)
        )
        metrics = ["impressions", "clicks", "ctr"]
        dimensions = ["campaign"]

        # Test default number of rows
        data = generate_metrics_data(date_range, metrics)
        self.assertEqual(len(data), 10)

        # Test custom number of rows
        data = generate_metrics_data(date_range, metrics, num_rows=5)
        self.assertEqual(len(data), 5)

        # Test data structure
        data = generate_metrics_data(
            date_range, metrics, dimensions, num_rows=1
        )
        self.assertIn("date", data[0])
        self.assertIn("campaign", data[0])
        for metric in metrics:
            self.assertIn(metric, data[0])

        # Test data types
        self.assertIsInstance(data[0]["impressions"], int)
        self.assertIsInstance(data[0]["clicks"], int)
        self.assertIsInstance(data[0]["ctr"], float)

    def test_mock_facebook_campaign_response(self):
        """Test mock_facebook_campaign_response function."""
        response = mock_facebook_campaign_response()

        # Check structure
        self.assertIn("data", response)
        self.assertIn("paging", response)
        self.assertIn("cursors", response["paging"])

        # Check data content
        self.assertEqual(len(response["data"]), 5)
        for i, campaign in enumerate(response["data"], 1):
            self.assertEqual(campaign["id"], f"campaign_{i}")
            self.assertEqual(campaign["name"], f"Campaign {i}")

    def test_mock_facebook_metrics_response(self):
        """Test mock_facebook_metrics_response function."""
        metrics = ["impressions", "clicks", "ctr"]
        response = mock_facebook_metrics_response(metrics)

        # Check structure
        self.assertIn("data", response)
        self.assertIn("summary", response)

        # Check data content
        self.assertGreater(len(response["data"]), 0)
        for row in response["data"]:
            for metric in metrics:
                self.assertIn(metric, row)

        # Check summary content
        for metric in metrics:
            if metric not in ["ctr", "cvr"]:
                self.assertIn(metric, response["summary"])

    def test_mock_google_campaign_response(self):
        """Test mock_google_campaign_response function."""
        response = mock_google_campaign_response()

        # Check structure
        self.assertIn("results", response)
        self.assertIn("nextPageToken", response)

        # Check data content
        self.assertEqual(len(response["results"]), 5)
        for i, result in enumerate(response["results"], 1):
            self.assertIn("campaign", result)
            self.assertEqual(result["campaign"]["id"], f"{i}")
            self.assertEqual(result["campaign"]["name"], f"Google Campaign {i}")


if __name__ == "__main__":
    unittest.main()
