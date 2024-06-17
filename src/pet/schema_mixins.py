from typing import ClassVar
import re

from pydantic import field_validator


class PetValidationMixin:
    LETTER_MATCH_PATTERN: ClassVar[re.Pattern] = re.compile(r"^[а-яА-Яa-zA-Z\- ]+$")
    MIN_WEIGHT: ClassVar[re.Pattern] = 0

    @field_validator("name", check_fields=False)
    @classmethod
    def validate_name(cls, name: str):
        if not re.match(cls.LETTER_MATCH_PATTERN, name):
            raise ValueError("Pet name contains incorrect symbols")
        return name

    @field_validator("species", check_fields=False)
    @classmethod
    def validate_species(cls, species: str):
        if not re.match(cls.LETTER_MATCH_PATTERN, species):
            raise ValueError("Species contains incorrect symbols")
        return species

    @field_validator("breed", check_fields=False)
    @classmethod
    def validate_breed(cls, breed: str):
        if not re.match(cls.LETTER_MATCH_PATTERN, breed):
            raise ValueError("Species contains incorrect symbols")
        return breed

    @field_validator("weight", check_fields=False)
    @classmethod
    def validate_weight(cls, weight: float):
        if weight <= cls.MIN_WEIGHT:
            raise ValueError("Weight can only be a positive number")
        return weight
