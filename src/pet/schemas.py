from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from src.pet.models import PetGenderEnum


class PetDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=30)
    species: str = Field(..., max_length=30)
    breed: Optional[str] = Field(None, max_length=30)
    gender: PetGenderEnum
    weight: Optional[float] = None
    