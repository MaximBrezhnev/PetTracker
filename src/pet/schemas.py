from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from src.event.schemas import ShowEventSchema
from src.pet.models import PetGenderEnum
from src.pet.schema_mixins import PetValidationMixin


class PetCreationSchema(PetValidationMixin, BaseModel):
    """Schema representing data for pet creation"""

    name: str = Field(..., min_length=1, max_length=30)
    species: str = Field(..., min_length=1, max_length=30)
    breed: Optional[str] = Field(None, min_length=1, max_length=30)
    gender: PetGenderEnum
    weight: Optional[float] = None


class ShowPetSchema(BaseModel):
    """Schema representing general information about a pet"""

    pet_id: UUID
    name: str


class ShowPetInDetailSchema(BaseModel):
    """Schema representing detailed information about a pet"""

    model_config = ConfigDict(from_attributes=True)

    pet_id: UUID
    name: str
    species: str
    breed: Optional[str] = None
    gender: PetGenderEnum
    weight: Optional[float] = None
    events: List[ShowEventSchema] = None


class UpdatePetSchema(PetValidationMixin, BaseModel):
    """Schema representing data for pet update"""

    name: Optional[str] = Field(None, min_length=1, max_length=30)
    species: Optional[str] = Field(None, min_length=1, max_length=30)
    breed: Optional[str] = Field(None, min_length=1, max_length=30)
    gender: Optional[PetGenderEnum] = None
    weight: Optional[float] = None
