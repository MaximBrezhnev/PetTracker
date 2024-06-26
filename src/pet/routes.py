from typing import List
from typing import Optional
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from starlette.responses import JSONResponse

from src.dependencies import get_current_user
from src.pet.dependencies import get_pet_service
from src.pet.models import Pet
from src.pet.schemas import PetCreationSchema
from src.pet.schemas import ShowPetInDetailSchema
from src.pet.schemas import ShowPetSchema
from src.pet.schemas import UpdatePetSchema
from src.pet.services.services import PetService
from src.user.models import User


pet_router: APIRouter = APIRouter(
    prefix="/pet",
    tags=[
        "pet",
    ],
)


@pet_router.post("/", response_model=ShowPetInDetailSchema)
async def add_pet(
    body: PetCreationSchema,
    user: User = Depends(get_current_user),
    pet_service: PetService = Depends(get_pet_service),
) -> Pet:
    """Endpoint that adds a new pet to the current user"""

    pet: Pet = await pet_service.add_pet(
        user=user,
        name=body.name,
        species=body.species,
        breed=body.breed,
        gender=body.gender,
        weight=body.weight,
    )

    return ShowPetInDetailSchema(
        pet_id=pet.pet_id,
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        gender=pet.gender,
        weight=pet.weight,
        events=[],
    )


@pet_router.get("/", response_model=ShowPetInDetailSchema)
async def get_pet(
    pet_id: UUID,
    user: User = Depends(get_current_user),
    pet_service: PetService = Depends(get_pet_service),
) -> ShowPetInDetailSchema:
    """Endpoint that returns a pet with the provided id"""

    pet, events = await pet_service.get_pet_by_id(pet_id=pet_id, user_id=user.user_id)

    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pet with this id not found"
        )

    return ShowPetInDetailSchema(
        pet_id=pet.pet_id,
        name=pet.name,
        species=pet.species,
        breed=pet.breed,
        gender=pet.gender,
        weight=pet.weight,
        events=events,
    )


@pet_router.get("/list-of-pets", response_model=List[ShowPetSchema])
async def get_list_of_pets(
    user: User = Depends(get_current_user),
    pet_service: PetService = Depends(get_pet_service),
) -> List[Pet]:
    """Endpoint that returns list of pets belonged to the current user"""

    pets: List[Pet] = await pet_service.get_list_of_pets(user=user)

    if not pets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="This user does not have pets"
        )

    return pets


@pet_router.delete("/")
async def delete_pet(
    pet_id: UUID,
    user: User = Depends(get_current_user),
    pet_service: PetService = Depends(get_pet_service),
) -> JSONResponse:
    """Endpoint that deletes pet with provided id"""

    try:
        await pet_service.delete_pet_by_id(pet_id=pet_id, user_id=user.user_id)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Pet was deleted successfully"},
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet with this id belonging to the current user not found",
        )


@pet_router.patch("/", response_model=ShowPetInDetailSchema)
async def update_pet(
    pet_id: UUID,
    body: UpdatePetSchema,
    user: User = Depends(get_current_user),
    pet_service: PetService = Depends(get_pet_service),
) -> Pet:
    """Endpoint that updates a pet with the provided id
    using the provided data"""

    parameters_for_update: dict = body.model_dump(exclude_none=True)

    if not parameters_for_update:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one parameter must be provided",
        )

    updated_pet: Optional[Pet] = await pet_service.update_pet(
        user_id=user.user_id,
        pet_id=pet_id,
        parameters_for_update=parameters_for_update,
    )
    if updated_pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pet with this id not found"
        )

    return updated_pet
