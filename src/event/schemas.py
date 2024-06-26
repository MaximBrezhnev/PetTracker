from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from src.event.schema_mixins import EventValidationMixin


class EventCreationSchema(EventValidationMixin, BaseModel):
    """
    Schema representing data for event creation with
    the date passed as separate elements. Schema also includes
    parameter timezone for correct work with the provided date
    """

    title: str = Field(..., min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1, max_length=300)
    year: int
    month: int
    day: int
    hour: int
    minute: int

    timezone: str
    pet_id: UUID


class ShowEventSchema(BaseModel):
    """
    Schema representing information about event.
    Moreover, if a detailed representation is not needed,
    then the "content" parameter may not be passed
    """

    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    pet_id: UUID
    title: str
    content: Optional[str] = None
    year: int
    month: int
    day: int
    hour: int
    minute: int
    is_happened: bool


class UpdateEventSchema(EventValidationMixin, BaseModel):
    """
    Schema representing data for event update with
    the date passed as separate elements. Schema also includes
    parameter timezone for correct work with the provided date
    """

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1, max_length=300)
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None

    timezone: str
