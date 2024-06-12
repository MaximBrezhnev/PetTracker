from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.pet.models import Pet
from src.pet.schemas import PetCreationDTO
from src.pet.services.dal_services import create_pet, get_pet, get_pets, delete_pet, update_pet
from src.user.models import User


async def add_pet_service(body: PetCreationDTO, user: User, db_session: AsyncSession) -> Pet:
    pet: Pet = await create_pet(body, user, db_session)
    return pet


async def get_pet_service(pet_id, db_session: AsyncSession) -> Optional[Pet]:
    pet: Optional[Pet] = await get_pet(pet_id, db_session)
    return pet


async def get_list_of_pets_service(
        user: User,
        db_session: AsyncSession
) -> List[Pet]:
    pets: List[Pet] = await get_pets(user, db_session)
    return pets


async def delete_pet_service(
        pet_id: str,
        db_session: AsyncSession
) -> None:
    pet: Optional[Pet] = await get_pet(pet_id, db_session)
    if pet is None:
        raise ValueError("Pet with this id does not exist")

    await delete_pet(pet, db_session)


async def update_pet_service(
        pet_id: str,
        parameters_for_update: dict,
        db_session: AsyncSession
) -> Pet:
    pet: Optional[Pet] = await get_pet(pet_id, db_session)

    if pet is None:
        raise ValueError("Pet with this id does not exist")

    updated_pet = await update_pet(pet, parameters_for_update, db_session)

    return updated_pet



