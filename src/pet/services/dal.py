from typing import List
from typing import Optional
from uuid import UUID

from sqlalchemy import Result
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.pet.models import Pet
from src.pet.models import PetGenderEnum
from src.services import BaseDAL
from src.user.models import User


class PetDAL(BaseDAL):
    """Data access layer service that enables to work with pet data"""

    async def create_pet(
        self,
        user: User,
        name: str,
        species: str,
        breed: Optional[str],
        gender: PetGenderEnum,
        weight: int,
    ) -> Pet:
        """Creates a new pet in database"""

        async with self.db_session.begin():
            pet: Pet = Pet(
                name=name,
                species=species,
                breed=breed,
                gender=gender,
                weight=weight,
                owner_id=user.user_id,
                owner=user,
            )
            self.db_session.add(pet)
            await self.db_session.flush()

            return pet

    async def get_pet(self, pet_id: UUID, user_id: UUID) -> Optional[Pet]:
        """Gets a pet from database by the provided id.
        In addition, loads events related to this pet"""

        async with self.db_session.begin():
            result: Result = await self.db_session.execute(
                select(Pet)
                .filter_by(pet_id=pet_id, owner_id=user_id)
                .options(selectinload(Pet.events))
            )
            return result.scalars().first()

    async def get_pets(self, user: User) -> List[Pet]:
        """Gets a list of pets belonged to the provided user from database"""

        async with self.db_session.begin():
            result: Result = await self.db_session.execute(
                select(Pet).filter_by(owner_id=user.user_id)
            )

            return result.scalars().all()

    async def delete_pet(self, pet: Pet) -> None:
        """Deletes the provided pass from database"""

        async with self.db_session.begin():
            await self.db_session.delete(pet)

    async def update_pet(
        self,
        pet: Pet,
        parameters_for_update: dict,
    ) -> Pet:
        """Updates a pet using the provided parameters for update"""

        async with self.db_session.begin():
            for key, value in parameters_for_update.items():
                setattr(pet, key, value)

            return pet
