from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import JSONResponse

from src.dependencies import get_current_user
from src.pet.models import Pet
from src.pet.schemas import PetCreationSchema, ShowPetInDetailSchema, UpdatePetSchema, ShowPetSchema
from src.pet.services.services2 import PetService
from src.user.models import User
from src.pet.dependencies import get_pet_service


pet_router = APIRouter(
    prefix="/pet",
    tags=["pet", ]
)


@pet_router.post("/", response_model=ShowPetInDetailSchema)
async def add_pet(
        body: PetCreationSchema,
        user: User = Depends(get_current_user),
        pet_service: PetService = Depends(get_pet_service)
) -> Pet:
    pet: Pet = await pet_service.add_pet(
        user=user,
        name=body.name,
        species=body.species,
        breed=body.breed,
        gender=body.gender,
        weight=body.weight
    )

    return pet


@pet_router.get("/", response_model=ShowPetInDetailSchema)  # Обдумать
async def get_pet(
        pet_id: str,
        user: User = Depends(get_current_user),
        pet_service: PetService = Depends(get_pet_service),
) -> ShowPetInDetailSchema:
    pet, events = await pet_service.get_pet_by_id(pet_id=pet_id)

    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet with this id not found"
        )

    return ShowPetInDetailSchema(
        pet_id=pet.pet_id,
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        gender=pet.gender,
        weight=pet.weight,
        events=events
    )


@pet_router.get("/list-of-pets", response_model=List[ShowPetSchema])
async def get_list_of_pets(
        user: User = Depends(get_current_user),
        pet_service: PetService = Depends(get_pet_service)
) -> List[Pet]:
    pets: List[Pet] = await pet_service.get_list_of_pets(user=user)

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
        pet_service: PetService = Depends(get_pet_service)
) -> JSONResponse:
    try:
        await pet_service.delete_pet_by_id(pet_id=pet_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Pet was deleted successfully"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet with this id not found"
        )


@pet_router.patch("/", response_model=ShowPetInDetailSchema)
async def update_pet(
        pet_id: str,
        body: UpdatePetSchema,
        user: User = Depends(get_current_user),
        pet_service: PetService = Depends(get_pet_service)
) -> Pet:
    parameters_for_update = body.dict(exclude_none=True)

    if not parameters_for_update:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one parameter must be provided"
        )

    try:
        updated_pet: Pet = await pet_service.update_pet(
            pet_id,
            parameters_for_update,
        )
        return updated_pet

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet with this id not found"
        )


