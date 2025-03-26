"""Date handling utilities cho Digital Metrics API."""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Union

from app.models.core import DateRange

DEFAULT_DATE_FORMAT = "%Y-%m-%d"


def format_date(
    date: Union[datetime, str], output_format: str = DEFAULT_DATE_FORMAT
) -> str:
    """
    Chuẩn hóa date thành string theo định dạng cụ thể.

    Args:
        date: Ngày để format, có thể là datetime hoặc string
        output_format: Định dạng output string mong muốn

    Returns:
        String ngày đã được format

    Examples:
        >>> format_date(datetime(2023, 1, 15))
        '2023-01-15'
        >>> format_date(datetime(2023, 1, 15), "%d/%m/%Y")
        '15/01/2023'
        >>> format_date("2023-01-15")
        '2023-01-15'
    """
    if isinstance(date, str):
        date = parse_date(date)
    return date.strftime(output_format)


def parse_date(date_str: str, input_format: Optional[str] = None) -> datetime:
    """
    Parse date string thành datetime object.

    Args:
        date_str: String ngày cần parse
        input_format: Định dạng của input string (optional)

    Returns:
        Datetime object

    Raises:
        ValueError: Khi không thể parse date string

    Examples:
        >>> parse_date("2023-01-15")
        datetime.datetime(2023, 1, 15, 0, 0)
        >>> parse_date("15/01/2023", "%d/%m/%Y")
        datetime.datetime(2023, 1, 15, 0, 0)
    """
    if input_format:
        return datetime.strptime(date_str, input_format)

    # Try common formats
    formats = [DEFAULT_DATE_FORMAT, "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Cannot parse date string: {date_str}")


def validate_date_range(
    start_date: Union[datetime, str], end_date: Union[datetime, str]
) -> Tuple[datetime, datetime]:
    """
    Validate date range và trả về tuple of datetime objects.

    Args:
        start_date: Ngày bắt đầu, có thể là datetime hoặc string
        end_date: Ngày kết thúc, có thể là datetime hoặc string

    Returns:
        Tuple of (start_date, end_date) as datetime objects

    Raises:
        ValueError: Khi end_date < start_date

    Examples:
        >>> validate_date_range("2023-01-01", "2023-01-31")
        (datetime.datetime(2023, 1, 1, 0, 0), datetime.datetime(2023, 1, 31, 0, 0))
    """
    if isinstance(start_date, str):
        start_date = parse_date(start_date)

    if isinstance(end_date, str):
        end_date = parse_date(end_date)

    if end_date < start_date:
        raise ValueError("End date must be after start date")

    return start_date, end_date


def get_date_diff_days(
    start_date: Union[datetime, str], end_date: Union[datetime, str]
) -> int:
    """
    Tính số ngày giữa hai dates.

    Args:
        start_date: Ngày bắt đầu, có thể là datetime hoặc string
        end_date: Ngày kết thúc, có thể là datetime hoặc string

    Returns:
        Số ngày chênh lệch (int)

    Examples:
        >>> get_date_diff_days("2023-01-01", "2023-01-31")
        30
    """
    start, end = validate_date_range(start_date, end_date)
    return (end - start).days


def get_previous_period(date_range: DateRange) -> DateRange:
    """
    Tính previous period với cùng độ dài.

    Args:
        date_range: DateRange object hiện tại

    Returns:
        DateRange object cho previous period

    Examples:
        >>> current = DateRange(start_date=datetime(2023, 1, 1), end_date=datetime(2023, 1, 31))
        >>> prev = get_previous_period(current)
        >>> prev.start_date
        datetime.datetime(2022, 12, 1, 0, 0)
        >>> prev.end_date
        datetime.datetime(2022, 12, 31, 0, 0)
    """
    delta = date_range.end_date - date_range.start_date

    prev_end = date_range.start_date - timedelta(days=1)
    prev_start = prev_end - delta

    return DateRange(start_date=prev_start, end_date=prev_end)
