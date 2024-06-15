from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.event.mixins import EventValidationMixin


class EventCreationDTO(EventValidationMixin, BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: Optional[str] = Field(None,  min_length=1, max_length=300)
    year: int
    month: int
    day: int
    hour: int
    minute: int

    timezone: str
    pet_id: UUID


class ShowEventDTO(BaseModel):
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


class UpdateEventDTO(EventValidationMixin, BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None,  min_length=1, max_length=300)
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None

    timezone: str

