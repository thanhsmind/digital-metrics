"""Date-related models cho Digital Metrics API."""

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class DateRangePreset(str, Enum):
    """Preset date ranges để đơn giản hóa việc chọn khoảng thời gian."""

    TODAY = "TODAY"
    YESTERDAY = "YESTERDAY"
    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_14_DAYS = "LAST_14_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"
    LAST_90_DAYS = "LAST_90_DAYS"
    THIS_MONTH = "THIS_MONTH"
    LAST_MONTH = "LAST_MONTH"
    THIS_QUARTER = "THIS_QUARTER"
    LAST_QUARTER = "LAST_QUARTER"
    THIS_YEAR = "THIS_YEAR"
    LAST_YEAR = "LAST_YEAR"


class DateRange(BaseModel):
    """Model for date range specification."""

    start_date: Optional[date] = Field(None, description="Ngày bắt đầu")
    end_date: Optional[date] = Field(None, description="Ngày kết thúc")
    preset: Optional[DateRangePreset] = Field(
        None, description="Preset date range"
    )

    @validator("end_date")
    def end_date_after_start_date(cls, v, values):
        """Validate end_date is after start_date."""
        if "start_date" in values and values["start_date"] and v:
            if v < values["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v

    def get_date_range(self) -> tuple[date, date]:
        """
        Get start and end dates giải quyết preset nếu sử dụng.

        Returns:
            Tuple (start_date, end_date)
        """
        if self.preset:
            return self._resolve_preset(self.preset)

        if self.start_date and self.end_date:
            return self.start_date, self.end_date

        # Default to last 30 days if nothing specified
        today = datetime.now().date()
        return today - timedelta(days=30), today

    def _resolve_preset(self, preset: DateRangePreset) -> tuple[date, date]:
        """
        Convert preset to actual date range.

        Args:
            preset: DateRangePreset enum value

        Returns:
            Tuple (start_date, end_date)
        """
        today = datetime.now().date()

        if preset == DateRangePreset.TODAY:
            return today, today

        if preset == DateRangePreset.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday

        if preset == DateRangePreset.LAST_7_DAYS:
            return today - timedelta(days=7), today

        if preset == DateRangePreset.LAST_14_DAYS:
            return today - timedelta(days=14), today

        if preset == DateRangePreset.LAST_30_DAYS:
            return today - timedelta(days=30), today

        if preset == DateRangePreset.LAST_90_DAYS:
            return today - timedelta(days=90), today

        if preset == DateRangePreset.THIS_MONTH:
            start = date(today.year, today.month, 1)
            return start, today

        if preset == DateRangePreset.LAST_MONTH:
            if today.month == 1:
                start = date(today.year - 1, 12, 1)
                end = date(today.year, today.month, 1) - timedelta(days=1)
            else:
                start = date(today.year, today.month - 1, 1)
                end = date(today.year, today.month, 1) - timedelta(days=1)
            return start, end

        if preset == DateRangePreset.THIS_QUARTER:
            quarter = (today.month - 1) // 3
            start = date(today.year, quarter * 3 + 1, 1)
            return start, today

        if preset == DateRangePreset.LAST_QUARTER:
            quarter = (today.month - 1) // 3
            if quarter == 0:
                start = date(today.year - 1, 10, 1)
                end = date(today.year, 1, 1) - timedelta(days=1)
            else:
                start = date(today.year, (quarter - 1) * 3 + 1, 1)
                end = date(today.year, quarter * 3 + 1, 1) - timedelta(days=1)
            return start, end

        if preset == DateRangePreset.THIS_YEAR:
            start = date(today.year, 1, 1)
            return start, today

        if preset == DateRangePreset.LAST_YEAR:
            start = date(today.year - 1, 1, 1)
            end = date(today.year, 1, 1) - timedelta(days=1)
            return start, end

        # Default to last 30 days
        return today - timedelta(days=30), today
