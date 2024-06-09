from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session, get_current_user
from src.pet.models import Pet
from src.pet.schemas import PetDTO
from src.pet.services import add_pet_service
from src.user.models import User

pet_router = APIRouter(prefix="/pet")


@pet_router.post("/", response_model=PetDTO)
async def add_pet(
        body: PetDTO,
        db_session: AsyncSession = Depends(get_db_session),
        user: User = Depends(get_current_user)
) -> PetDTO:
    pet: Pet = await add_pet_service(body, user, db_session)
    return pet

