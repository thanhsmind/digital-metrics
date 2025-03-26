"""Formatting utilities cho Digital Metrics API."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union


def format_date(
    date_obj: Union[date, datetime], format_str: str = "%Y-%m-%d"
) -> str:
    """
    Format datetime hoặc date object thành string.

    Args:
        date_obj: Datetime hoặc date object cần format
        format_str: Format string (mặc định ISO format %Y-%m-%d)

    Returns:
        Formatted date string

    Examples:
        >>> from datetime import datetime
        >>> date_obj = datetime(2023, 1, 15)
        >>> format_date(date_obj)
        '2023-01-15'
        >>> format_date(date_obj, "%d/%m/%Y")
        '15/01/2023'
    """
    return date_obj.strftime(format_str)


def format_currency(
    value: Union[int, float], currency: str = "$", decimal_places: int = 2
) -> str:
    """
    Format số thành định dạng tiền tệ.

    Args:
        value: Giá trị cần format
        currency: Symbol tiền tệ (mặc định: $)
        decimal_places: Số chữ số thập phân (mặc định: 2)

    Returns:
        Formatted currency string

    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(1234.56, currency="₫", decimal_places=0)
        '₫1,235'
    """
    if decimal_places == 0:
        # Làm tròn nếu không có chữ số thập phân
        value = round(value)
        format_str = f"{currency}{value:,.0f}"
    else:
        format_str = f"{currency}{value:,.{decimal_places}f}"

    return format_str


def format_percent(value: Union[int, float], decimal_places: int = 2) -> str:
    """
    Format số thành định dạng phần trăm.

    Args:
        value: Giá trị cần format (0.1 = 10%)
        decimal_places: Số chữ số thập phân (mặc định: 2)

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percent(0.1234)
        '12.34%'
        >>> format_percent(0.5, decimal_places=0)
        '50%'
    """
    percentage = value * 100
    if decimal_places == 0:
        return f"{round(percentage)}%"
    else:
        return f"{percentage:.{decimal_places}f}%"


def format_large_number(
    value: Union[int, float], decimal_places: int = 1
) -> str:
    """
    Format số lớn thành định dạng đọc được (K, M, B).

    Args:
        value: Giá trị cần format
        decimal_places: Số chữ số thập phân (mặc định: 1)

    Returns:
        Formatted number string

    Examples:
        >>> format_large_number(1234)
        '1.2K'
        >>> format_large_number(1200000)
        '1.2M'
        >>> format_large_number(2500000000)
        '2.5B'
    """
    if value < 1000:
        return str(value)

    for unit in ["", "K", "M", "B", "T"]:
        if abs(value) < 1000:
            if unit == "":
                return str(int(value))
            return f"{value:.{decimal_places}f}{unit}"
        value /= 1000

    return f"{value:.{decimal_places}f}T"


def format_metrics_data(
    data: List[Dict[str, Any]], formatters: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Format một list của metrics data dựa trên quy tắc format.

    Args:
        data: List các dict với metric data
        formatters: Dict với keys là tên metric và values là formatter type
                   ('currency', 'percent', 'large_number', 'date')

    Returns:
        List các dict với formatted metric data

    Examples:
        >>> data = [
        ...     {"date": "2023-01-01", "impressions": 1234, "ctr": 0.0234, "spend": 123.45},
        ...     {"date": "2023-01-02", "impressions": 2345, "ctr": 0.0345, "spend": 234.56}
        ... ]
        >>> formatters = {
        ...     "impressions": "large_number",
        ...     "ctr": "percent",
        ...     "spend": "currency"
        ... }
        >>> formatted = format_metrics_data(data, formatters)
        >>> formatted[0]["impressions"]
        '1.2K'
        >>> formatted[0]["ctr"]
        '2.34%'
        >>> formatted[0]["spend"]
        '$123.45'
    """
    formatted_data = []

    for item in data:
        formatted_item = {}

        for key, value in item.items():
            if key in formatters:
                formatter_type = formatters[key]

                if formatter_type == "currency":
                    formatted_value = format_currency(value)
                elif formatter_type == "percent":
                    formatted_value = format_percent(value)
                elif formatter_type == "large_number":
                    formatted_value = format_large_number(value)
                elif formatter_type == "date" and isinstance(
                    value, (date, datetime)
                ):
                    formatted_value = format_date(value)
                else:
                    formatted_value = value

                formatted_item[key] = formatted_value
            else:
                formatted_item[key] = value

        formatted_data.append(formatted_item)

    return formatted_data


def camel_to_snake(s: str) -> str:
    """
    Convert camelCase string thành snake_case.

    Args:
        s: camelCase string

    Returns:
        snake_case string

    Examples:
        >>> camel_to_snake("helloWorld")
        'hello_world'
        >>> camel_to_snake("HelloWorld")
        'hello_world'
        >>> camel_to_snake("APIResponse")
        'api_response'
    """
    # Handle first character
    result = s[0].lower()

    # Process remaining characters
    for char in s[1:]:
        if char.isupper():
            result += "_" + char.lower()
        else:
            result += char

    return result


def snake_to_camel(s: str) -> str:
    """
    Convert snake_case string thành camelCase.

    Args:
        s: snake_case string

    Returns:
        camelCase string

    Examples:
        >>> snake_to_camel("hello_world")
        'helloWorld'
        >>> snake_to_camel("api_response")
        'apiResponse'
    """
    # Split on underscores
    components = s.split("_")

    # Join back with next word capitalized
    return components[0] + "".join(x.title() for x in components[1:])


def convert_keys(data: Any, converter: callable) -> Any:
    """
    Convert tất cả keys trong dict hoặc list of dicts.

    Args:
        data: Dict hoặc list of dicts
        converter: Function để convert keys (như camel_to_snake hoặc snake_to_camel)

    Returns:
        Data với converted keys

    Examples:
        >>> data = {"firstName": "John", "lastName": "Doe", "userAddress": {"streetName": "Main"}}
        >>> convert_keys(data, camel_to_snake)
        {'first_name': 'John', 'last_name': 'Doe', 'user_address': {'street_name': 'Main'}}

        >>> data = {"first_name": "John", "last_name": "Doe"}
        >>> convert_keys(data, snake_to_camel)
        {'firstName': 'John', 'lastName': 'Doe'}
    """
    if isinstance(data, dict):
        return {
            converter(key): convert_keys(value, converter)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [convert_keys(item, converter) for item in data]
    else:
        return data


def to_snake_case(data: Any) -> Any:
    """
    Convert tất cả keys trong dict hoặc list of dicts thành snake_case.

    Args:
        data: Dict hoặc list with camelCase keys

    Returns:
        Data với snake_case keys
    """
    return convert_keys(data, camel_to_snake)


def to_camel_case(data: Any) -> Any:
    """
    Convert tất cả keys trong dict hoặc list of dicts thành camelCase.

    Args:
        data: Dict hoặc list with snake_case keys

    Returns:
        Data với camelCase keys
    """
    return convert_keys(data, snake_to_camel)
