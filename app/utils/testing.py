"""Testing utilities cho Digital Metrics API."""

import json
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from app.models.core import DateRange, MetricsFilter

# Test data generators


def generate_date_range(days_ago: int = 30, days_range: int = 30) -> DateRange:
    """
    Generate DateRange từ X days ago cho Y days.

    Args:
        days_ago: Số ngày trước hiện tại để bắt đầu range
        days_range: Số ngày trong range

    Returns:
        DateRange object

    Examples:
        >>> range = generate_date_range(30, 7)
        >>> (range.end_date - range.start_date).days
        7
    """
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=days_ago)
    end_date = start_date + timedelta(days=days_range)

    return DateRange(start_date=start_date, end_date=end_date)


def generate_metrics_filter(
    metrics: Optional[List[str]] = None, dimensions: Optional[List[str]] = None
) -> MetricsFilter:
    """
    Generate MetricsFilter với metrics và dimensions cụ thể.

    Args:
        metrics: List các metrics
        dimensions: List các dimensions

    Returns:
        MetricsFilter object

    Examples:
        >>> filter = generate_metrics_filter(["impressions", "clicks"])
        >>> filter.metrics
        ['impressions', 'clicks']
    """
    if metrics is None:
        metrics = ["impressions", "clicks", "ctr", "spend"]

    return MetricsFilter(
        date_range=generate_date_range(), metrics=metrics, dimensions=dimensions
    )


def generate_metrics_data(
    date_range: DateRange,
    metrics: List[str],
    dimensions: Optional[List[str]] = None,
    num_rows: int = 10,
) -> List[Dict[str, Any]]:
    """
    Generate fake metrics data.

    Args:
        date_range: Khoảng thời gian cho data
        metrics: List các metrics cần generate
        dimensions: List các dimensions (optional)
        num_rows: Số rows cần generate

    Returns:
        List các metrics data points

    Examples:
        >>> from datetime import datetime
        >>> range = DateRange(start_date=datetime(2023, 1, 1), end_date=datetime(2023, 1, 7))
        >>> data = generate_metrics_data(range, ["impressions", "clicks"], num_rows=2)
        >>> len(data)
        2
        >>> "impressions" in data[0]
        True
    """
    data = []
    current_date = date_range.start_date
    delta = (date_range.end_date - date_range.start_date).days

    for _ in range(num_rows):
        row = {}

        # Add date dimension
        random_day = random.randint(0, delta)
        row_date = current_date + timedelta(days=random_day)
        row["date"] = row_date.strftime("%Y-%m-%d")

        # Add custom dimensions
        if dimensions:
            for dim in dimensions:
                row[dim] = f"{dim}_{random.randint(1, 5)}"

        # Add metrics
        for metric in metrics:
            if metric in ["ctr", "cvr"]:
                row[metric] = round(random.uniform(0.01, 0.1), 4)
            else:
                row[metric] = random.randint(100, 10000)

        data.append(row)

    return data


# Mock response generators


def mock_facebook_campaign_response() -> Dict[str, Any]:
    """
    Generate mock Facebook campaigns API response.

    Returns:
        Dictionary giống Facebook API response

    Examples:
        >>> response = mock_facebook_campaign_response()
        >>> len(response["data"])
        5
    """
    return {
        "data": [
            {"id": f"campaign_{i}", "name": f"Campaign {i}"}
            for i in range(1, 6)
        ],
        "paging": {
            "cursors": {"before": "MAZDZD", "after": "MTNDY2"},
            "next": "https://graph.facebook.com/v13.0/next_page",
        },
    }


def mock_facebook_metrics_response(metrics: List[str]) -> Dict[str, Any]:
    """
    Generate mock Facebook metrics API response.

    Args:
        metrics: List các metrics cần include

    Returns:
        Dictionary giống Facebook metrics API response

    Examples:
        >>> response = mock_facebook_metrics_response(["impressions", "clicks"])
        >>> "data" in response
        True
        >>> "summary" in response
        True
    """
    date_range = generate_date_range()
    return {
        "data": generate_metrics_data(date_range, metrics),
        "summary": {
            metric: random.randint(1000, 100000)
            for metric in metrics
            if metric not in ["ctr", "cvr"]
        },
    }


def mock_google_campaign_response() -> Dict[str, Any]:
    """
    Generate mock Google campaigns API response.

    Returns:
        Dictionary giống Google Ads API response

    Examples:
        >>> response = mock_google_campaign_response()
        >>> len(response["results"])
        5
    """
    return {
        "results": [
            {
                "campaign": {
                    "resourceName": f"customers/123/campaigns/{i}",
                    "id": f"{i}",
                    "name": f"Google Campaign {i}",
                }
            }
            for i in range(1, 6)
        ],
        "nextPageToken": "abc123",
    }


# Test helper functions


def load_test_data(file_path: str) -> Any:
    """
    Load test data từ JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Data từ JSON file

    Raises:
        FileNotFoundError: Khi file không tồn tại
        json.JSONDecodeError: Khi file không phải valid JSON
    """
    with open(file_path, "r") as f:
        return json.load(f)


def validate_response_structure(
    response: Dict[str, Any], required_fields: List[str]
) -> bool:
    """
    Validate response chứa tất cả required fields.

    Args:
        response: Dictionary response cần check
        required_fields: List các fields phải có trong response

    Returns:
        True nếu tất cả fields tồn tại, False nếu không

    Examples:
        >>> response = {"data": [], "meta": {"page": 1}}
        >>> validate_response_structure(response, ["data", "meta"])
        True
        >>> validate_response_structure(response, ["data", "metadata"])
        False
    """
    return all(field in response for field in required_fields)
