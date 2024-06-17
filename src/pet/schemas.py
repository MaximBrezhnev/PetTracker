from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from typing import List

from src.event.schemas import ShowEventSchema
from src.pet.schema_mixins import PetValidationMixin
from src.pet.models import PetGenderEnum


class PetCreationSchema(PetValidationMixin, BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    species: str = Field(..., min_length=1, max_length=30)
    breed: Optional[str] = Field(None, min_length=1, max_length=30)
    gender: PetGenderEnum
    weight: Optional[float] = None


class ShowPetSchema(BaseModel):
    pet_id: UUID
    name: str


class ShowPetInDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pet_id: UUID
    name: str
    species: str
    breed: Optional[str] = None
    gender: PetGenderEnum
    weight: Optional[float] = None
    events: List[ShowEventSchema] = None


class UpdatePetSchema(PetValidationMixin, BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=30)
    species: Optional[str] = Field(None, min_length=1, max_length=30)
    breed: Optional[str] = Field(None, min_length=1, max_length=30)
    gender: Optional[PetGenderEnum] = None
    weight: Optional[float] = None


