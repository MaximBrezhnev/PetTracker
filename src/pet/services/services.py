import operator
from typing import List
from typing import Optional
from typing import Tuple
from uuid import UUID

from src.pet.models import Pet
from src.pet.models import PetGenderEnum
from src.services import BaseService
from src.user.models import User


class PetService(BaseService):
    """Service representing business logic
    used by the endpoints of pet_router"""

    async def add_pet(
        self,
        user: User,
        name: str,
        species: str,
        breed: str,
        gender: PetGenderEnum,
        weight: int,
    ) -> Tuple[Pet, List[dict]]:
        """Adds pet to the provided user"""

        pet: Pet = await self.dal.create_pet(
            user=user,
            name=name,
            species=species,
            breed=breed,
            gender=gender,
            weight=weight,
        )
        return pet

    async def get_pet_by_id(
        self, pet_id: UUID, user_id: UUID
    ) -> [Tuple[Optional[Pet], List[dict]]]:
        """Gets a pet by its id"""

        pet: Optional[Pet] = await self.dal.get_pet(pet_id=pet_id, user_id=user_id)

        if pet is None:
            return None, []

        return pet, self._form_event_data_for_pet(pet=pet)

    @staticmethod
    def _form_event_data_for_pet(pet: Pet) -> List[dict]:
        """Forms data containing a list of events belonged to the provided pet"""

        events = []
        for event in sorted(
            pet.events, key=operator.attrgetter("scheduled_at"), reverse=True
        ):
            events.append(
                {
                    "event_id": event.event_id,
                    "title": event.title,
                    "pet_id": event.pet_id,
                    "year": event.scheduled_at.year,
                    "month": event.scheduled_at.month,
                    "day": event.scheduled_at.day,
                    "hour": event.scheduled_at.hour,
                    "minute": event.scheduled_at.minute,
                    "is_happened": event.is_happened,
                }
            )
        return events

    async def get_list_of_pets(self, user: User) -> List[Pet]:
        """Gets a list of pets belonged to the provided user"""

        pets: List[Pet] = await self.dal.get_pets(user=user)
        return pets

    async def delete_pet_by_id(self, pet_id: UUID, user_id: UUID) -> None:
        """Deletes a pet with the provided id"""

        pet: Optional[Pet] = await self.dal.get_pet(pet_id=pet_id, user_id=user_id)
        if pet is None:
            raise ValueError("Pet with this id does not exist")

        await self.dal.delete_pet(pet=pet)

    async def update_pet(
        self, pet_id: UUID, user_id: UUID, parameters_for_update: dict
    ) -> Pet:
        """Updates a pet using the provided parameters for update"""

        pet: Optional[Pet] = await self.dal.get_pet(pet_id=pet_id, user_id=user_id)

        if pet is None:
            return

        updated_pet = await self.dal.update_pet(pet, parameters_for_update)

        return updated_pet
