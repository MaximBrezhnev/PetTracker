from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.pet.models import Pet, PetGenderEnum
from src.services import BaseDAL
from src.user.models import User


class PetDAL(BaseDAL):

    async def create_pet(
            self,
            user: User,
            name: str,
            species: str,
            breed: Optional[str],
            gender: PetGenderEnum,
            weight: int,
    ) -> Pet:
        pet: Pet = Pet(
            name=name,
            species=species,
            breed=breed,
            gender=gender,
            weight=weight,
            owner_id=user.user_id,
            owner=user
        )
        self.db_session.add(pet)
        await self.db_session.flush()

        return pet

    async def get_pet(self, pet_id: str) -> Optional[Pet]:
        result = await self.db_session.execute(
            select(Pet).filter_by(pet_id=pet_id).
            options(selectinload(Pet.events))
        )

        return result.scalars().first()

    async def get_pets(self, user: User) -> List[Pet]:
        result = await self.db_session.execute(
            select(Pet).filter_by(owner_id=user.user_id)
        )

        return result.scalars().all()

    async def delete_pet(self, pet: Pet) -> None:
        await self.db_session.delete(pet)

    async def update_pet(
            self,
            pet: Pet,
            parameters_for_update: dict,
    ) -> Pet:
        async with self.db_session:
            for key, value in parameters_for_update.items():
                setattr(pet, key, value)

        return pet
