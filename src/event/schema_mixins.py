from datetime import datetime
from datetime import timedelta
from typing import Self

import pytz
from pydantic import field_validator
from pydantic import model_validator


class EventValidationMixin:
    """Mixin for the provided event data validation"""

    @field_validator("timezone", check_fields=False)
    @classmethod
    def validate_timezone(cls, timezone: str) -> str:
        """Checks if the provided timezone is in a list of valid timezones"""

        if timezone not in pytz.all_timezones:
            raise ValueError("Provided value is not a valid timezone name")

        return timezone

    @model_validator(mode="after")
    def validate_date(self) -> Self:
        """If date is provided, then checks whether the provided date
        is bigger than the current one"""

        if self.year and self.month and self.day and self.hour and self.minute:

            scheduled_at = datetime(
                year=self.year,
                month=self.month,
                day=self.day,
                hour=self.hour,
                minute=self.minute,
            )

            if scheduled_at < datetime.now() + timedelta(minutes=1):
                raise ValueError(
                    "Date must be greater than the current one " "by at least a minute"
                )

        return self
