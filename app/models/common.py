from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, validator


class DateRange(BaseModel):
    """
    Represents a date range with a start and end date.

    Attributes:
        start_date: The beginning date of the range (inclusive).
        end_date: The ending date of the range (inclusive).
    """

    start_date: date = Field(
        ..., description="The start date of the range (YYYY-MM-DD)."
    )
    end_date: date = Field(
        ..., description="The end date of the range (YYYY-MM-DD)."
    )

    @validator("end_date")
    def end_date_must_be_after_start_date(cls, v, values):
        """Validate that end_date is not before start_date."""
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("end_date must be on or after start_date")
        return v

    class Config:
        schema_extra = {
            "example": {"start_date": "2023-01-01", "end_date": "2023-01-31"}
        }


class OptionalDateRange(BaseModel):
    """
    Represents an optional date range where both start and end dates are optional.
    Used when a preset date range (like 'LAST_30_DAYS') can be used instead.

    Attributes:
        start_date: The beginning date of the range (inclusive), optional.
        end_date: The ending date of the range (inclusive), optional.
    """

    start_date: Optional[date] = Field(
        None,
        description="Optional start date (YYYY-MM-DD). Used if date_range is not provided.",
    )
    end_date: Optional[date] = Field(
        None,
        description="Optional end date (YYYY-MM-DD). Used if date_range is not provided.",
    )

    @validator("end_date")
    def end_date_must_be_after_start_date(cls, v, values):
        """Validate that end_date is not before start_date if both are provided."""
        if (
            v is not None
            and "start_date" in values
            and values["start_date"] is not None
            and v < values["start_date"]
        ):
            raise ValueError("end_date must be on or after start_date")
        return v

    class Config:
        schema_extra = {
            "example_both": {
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
            },
            "example_start_only": {
                "start_date": "2023-01-01",
                "end_date": None,
            },
            "example_end_only": {"start_date": None, "end_date": "2023-01-31"},
            "example_none": {"start_date": None, "end_date": None},
        }
