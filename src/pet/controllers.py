from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.dependencies import get_db_session, get_current_user
from src.pet.models import Pet
from src.pet.schemas import PetCreationDTO, ShowPetInDetailDTO, UpdatePetDTO, ShowPetDTO
from src.pet.services.services import add_pet_service, get_pet_service, get_list_of_pets_service, delete_pet_service, \
    update_pet_service
from src.user.models import User


pet_router = APIRouter(prefix="/pet")


@pet_router.post("/", response_model=ShowPetInDetailDTO)
async def add_pet(
        body: PetCreationDTO,
        db_session: AsyncSession = Depends(get_db_session),
        user: User = Depends(get_current_user)
) -> Pet:
    pet: Pet = await add_pet_service(body, user, db_session)
    return pet


@pet_router.get("/", response_model=ShowPetInDetailDTO)
async def get_pet(
        pet_id: str,
        db_session: AsyncSession = Depends(get_db_session),
        user: User = Depends(get_current_user)
) -> ShowPetInDetailDTO:
    pet, events = await get_pet_service(pet_id, db_session)

    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet with this id not found"
        )

    return ShowPetInDetailDTO(
        pet_id=pet.pet_id,
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        gender=pet.gender,
        weight=pet.weight,
        events=events
    )


@pet_router.get("/list-of-pets", response_model=List[ShowPetDTO])
async def get_list_of_pets(
        db_session: AsyncSession = Depends(get_db_session),
        user: User = Depends(get_current_user)
) -> List[Pet]:
    pets: List[Pet] = await get_list_of_pets_service(user, db_session)

    if not pets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This user does not have pets"
        )

    return pets


@pet_router.delete("/")
async def delete_pet(
        pet_id: str,
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    try:
        await delete_pet_service(pet_id, db_session)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Pet was deleted successfully"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet with this id not found"
        )


@pet_router.patch("/", response_model=ShowPetInDetailDTO)
async def update_pet(
        pet_id: str,
        body: UpdatePetDTO,
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)
) -> Pet:
    parameters_for_update = body.dict(exclude_none=True)

    if not parameters_for_update:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one parameter must be provided"
        )

    try:
        updated_pet: Pet = await update_pet_service(
            pet_id,
            parameters_for_update,
            db_session
        )
        return updated_pet
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet with this id not found"
        )


