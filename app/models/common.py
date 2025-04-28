from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, validator


class DateRange(BaseModel):
    """
    Represents a date range for querying metrics.

    Validates that end_date is not before start_date.
    """

    start_date: date
    end_date: date

    @validator("end_date")
    def end_date_must_not_be_before_start_date(cls, v, values):
        if "start_date" in values and v < values["start_date"]:
            raise ValueError("end_date must not be before start_date")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "start_date": date.today().isoformat(),
                "end_date": date.today().isoformat(),
            }
        }
    }


class OptionalDateRange(BaseModel):
    """
    Like DateRange, but allows start_date, end_date or both to be None.

    If both are provided, validates that end_date is not before start_date.
    """

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @validator("end_date")
    def end_date_must_not_be_before_start_date(cls, v, values):
        if (
            v is not None
            and "start_date" in values
            and values["start_date"] is not None
        ):
            if v < values["start_date"]:
                raise ValueError("end_date must not be before start_date")
        return v

    model_config = {
        "json_schema_extra": {
            "example_both": {
                "start_date": "2023-01-01",
                "end_date": "2023-01-31",
            },
            "example_start_only": {
                "start_date": "2023-01-01",
                "end_date": None,
            },
            "example_end_only": {
                "start_date": None,
                "end_date": "2023-01-31",
            },
            "example_none": {
                "start_date": None,
                "end_date": None,
            },
        }
    }
