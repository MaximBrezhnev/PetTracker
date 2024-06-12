from datetime import datetime, timedelta
from typing import Self

from pydantic import model_validator


class EventValidationMixin:
    @model_validator(mode="after")
    def validate_date(self) -> Self:
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
