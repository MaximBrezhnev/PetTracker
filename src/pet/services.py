from sqlalchemy.ext.asyncio import AsyncSession

from src.pet.models import Pet
from src.pet.schemas import PetDTO


async def add_pet_service(body: PetDTO, user, db_session: AsyncSession) -> Pet:
    async with db_session.begin():
        pet = Pet(
            name=body.name,
            species=body.species,
            breed=body.breed,
            gender=body.gender,
            weight=body.weight,
            owners=[user, ]
        )
        db_session.add(pet)
        await db_session.flush()

    return pet

