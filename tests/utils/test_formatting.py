"""Tests cho formatting utilities."""

import unittest
from datetime import datetime

from app.utils.formatting import (
    camel_to_snake,
    format_currency,
    format_date,
    format_large_number,
    format_metrics_data,
    format_percent,
    snake_to_camel,
)


class TestFormattingUtils(unittest.TestCase):
    """Test cases cho formatting utils."""

    def test_format_date(self):
        """Test format_date function."""
        date_obj = datetime(2023, 5, 15)

        # Test default format
        self.assertEqual(format_date(date_obj), "2023-05-15")

        # Test custom format
        self.assertEqual(format_date(date_obj, "%d/%m/%Y"), "15/05/2023")
        self.assertEqual(format_date(date_obj, "%Y-%m"), "2023-05")

    def test_format_currency(self):
        """Test format_currency function."""
        # Test default format
        self.assertEqual(format_currency(1234.56), "$1,234.56")

        # Test custom currency symbol
        self.assertEqual(format_currency(1234.56, currency="€"), "€1,234.56")

        # Test custom decimal places
        self.assertEqual(format_currency(1234.56, decimal_places=0), "$1,235")
        self.assertEqual(
            format_currency(1234.56, decimal_places=3), "$1,234.560"
        )

    def test_format_percent(self):
        """Test format_percent function."""
        # Test default format
        self.assertEqual(format_percent(0.1234), "12.34%")

        # Test custom decimal places
        self.assertEqual(format_percent(0.1234, decimal_places=0), "12%")
        self.assertEqual(format_percent(0.1234, decimal_places=3), "12.340%")

    def test_format_large_number(self):
        """Test format_large_number function."""
        # Test small numbers
        self.assertEqual(format_large_number(123), "123")

        # Test thousands
        self.assertEqual(format_large_number(1234), "1.2K")
        self.assertEqual(format_large_number(5678), "5.7K")

        # Test millions
        self.assertEqual(format_large_number(1234567), "1.2M")

        # Test billions
        self.assertEqual(format_large_number(1234567890), "1.2B")

        # Test custom decimal places
        self.assertEqual(
            format_large_number(1234567, decimal_places=2), "1.23M"
        )

    def test_format_metrics_data(self):
        """Test format_metrics_data function."""
        test_data = [
            {
                "date": "2023-01-01",
                "impressions": 12345,
                "clicks": 234,
                "ctr": 0.019,
                "spend": 123.45,
            },
            {
                "date": "2023-01-02",
                "impressions": 23456,
                "clicks": 345,
                "ctr": 0.0147,
                "spend": 234.56,
            },
        ]

        formatters = {
            "impressions": "large_number",
            "clicks": "large_number",
            "ctr": "percent",
            "spend": "currency",
        }

        formatted = format_metrics_data(test_data, formatters)

        # Check first row
        self.assertEqual(formatted[0]["impressions"], "12.3K")
        self.assertEqual(formatted[0]["clicks"], "234")
        self.assertEqual(formatted[0]["ctr"], "1.90%")
        self.assertEqual(formatted[0]["spend"], "$123.45")

        # Check second row
        self.assertEqual(formatted[1]["impressions"], "23.5K")
        self.assertEqual(formatted[1]["clicks"], "345")
        self.assertEqual(formatted[1]["ctr"], "1.47%")
        self.assertEqual(formatted[1]["spend"], "$234.56")

    def test_camel_to_snake(self):
        """Test camel_to_snake function."""
        self.assertEqual(camel_to_snake("helloWorld"), "hello_world")
        self.assertEqual(camel_to_snake("HelloWorld"), "hello_world")
        self.assertEqual(camel_to_snake("APIResponse"), "api_response")
        self.assertEqual(camel_to_snake("simpleText"), "simple_text")
        self.assertEqual(camel_to_snake("a"), "a")

    def test_snake_to_camel(self):
        """Test snake_to_camel function."""
        self.assertEqual(snake_to_camel("hello_world"), "helloWorld")
        self.assertEqual(snake_to_camel("api_response"), "apiResponse")
        self.assertEqual(snake_to_camel("simple_text"), "simpleText")
        self.assertEqual(snake_to_camel("a"), "a")


if __name__ == "__main__":
    unittest.main()
