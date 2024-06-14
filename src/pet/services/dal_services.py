from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.pet.models import Pet
from src.pet.schemas import PetCreationDTO
from src.user.models import User


async def create_pet(body: PetCreationDTO, user: User, db_session: AsyncSession) -> Pet:
    async with db_session.begin():
        pet = Pet(
            name=body.name,
            species=body.species,
            breed=body.breed,
            gender=body.gender,
            weight=body.weight,
            owner_id=user.user_id,
            owner=user
        )
        db_session.add(pet)
        await db_session.flush()

    return pet


async def get_pet(pet_id: str, db_session: AsyncSession) -> Optional[Pet]:
    async with db_session.begin():
        result = await db_session.execute(
            select(Pet).filter(Pet.pet_id == pet_id).
            options(selectinload(Pet.events))
        )

    return result.scalars().first()


async def get_pets(user: User, db_session: AsyncSession) -> List[Pet]:
    async with db_session.begin():
        result = await db_session.execute(
            select(Pet).filter(Pet.owner_id == user.user_id)
        )

    return result.scalars().all()


async def delete_pet(pet: Pet, db_session: AsyncSession) -> None:
    async with db_session.begin():
        await db_session.delete(pet)


async def update_pet(pet: Pet, parameters_for_update: dict, db_session: AsyncSession) -> Pet:
    async with db_session.begin():
        for key, value in parameters_for_update.items():
            setattr(pet, key, value)

    return pet