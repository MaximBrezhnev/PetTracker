from typing import Optional, List, Tuple
from uuid import UUID

from src.pet.models import Pet, PetGenderEnum
from src.services import BaseService
from src.user.models import User


class PetService(BaseService):

    async def add_pet(
            self,
            user: User,
            name: str,
            species: str,
            breed: str,
            gender: PetGenderEnum,
            weight: int
    ) -> Pet:
        pet: Pet = await self.dal.create_pet(
            user=user,
            name=name,
            species=species,
            breed=breed,
            gender=gender,
            weight=weight
        )
        return pet

    async def get_pet_by_id(self, pet_id: UUID) -> Optional[Tuple[Pet, List[dict]]]:
        pet: Optional[Pet] = await self.dal.get_pet(pet_id=pet_id)

        return pet, self._from_event_data_for_pet(pet=pet)

    @staticmethod
    def _from_event_data_for_pet(pet: Pet) -> List[dict]:
        events = []
        for event in pet.events:
            events.append(
                {
                    "event_id": event.event_id,
                    "title": event.title,
                    "content": event.content,
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
        pets: List[Pet] = await self.dal.get_pets(user=user)
        return pets

    async def delete_pet_by_id(self, pet_id: str) -> None:
        pet: Optional[Pet] = await self.dal.get_pet(pet_id=pet_id)
        if pet is None:
            raise ValueError("Pet with this id does not exist")

        await self.dal.delete_pet(pet=pet)

    async def update_pet(self, pet_id: str, parameters_for_update: dict) -> Pet:
        pet: Optional[Pet] = await self.dal.get_pet(pet_id=pet_id)

        if pet is None:
            raise ValueError("Pet with this id does not exist")

        updated_pet = await self.dal.update_pet(pet, parameters_for_update)

        return updated_pet
