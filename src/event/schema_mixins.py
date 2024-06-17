from datetime import datetime, timedelta
from typing import Self

import pytz
from pydantic import model_validator, field_validator


class EventValidationMixin:
    @field_validator("timezone", check_fields=False)
    @classmethod
    def validate_timezone(cls, timezone: str) -> str:
        if timezone not in pytz.all_timezones:
            raise ValueError("Provided value is not a valid timezone name")

        return timezone

    @model_validator(mode="after")
    def validate_date(self) -> Self:
        if self.year and self.month and self.day and self.hour and \
                self.minute:

            scheduled_at = datetime(
                year=self.year,
                month=self.month,
                day=self.day,
                hour=self.hour,
                minute=self.minute
            )

            if scheduled_at < datetime.now() + timedelta(minutes=1):
                raise ValueError("Date must be greater than the current one "
                                 "by at least a minute")

        return self
