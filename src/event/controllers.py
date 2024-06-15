from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.dependencies import get_current_user, get_db_session
from src.event.schemas import ShowEventDTO, EventCreationDTO, UpdateEventDTO
from src.event.services.services import create_event_service, get_event_service, get_list_of_events_service, \
    delete_event_service, update_event_service
from src.user.models import User


event_router = APIRouter(prefix="/event")


@event_router.post(path="/", response_model=ShowEventDTO)
async def create_event(
        body: EventCreationDTO,
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)
) -> ShowEventDTO:
    event_data: Optional[dict] = await create_event_service(
        body, user, db_session
    )

    if event_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not own the pet whose event to be created"
        )

    return ShowEventDTO(**event_data)


@event_router.get(path="/", response_model=ShowEventDTO)
async def get_event(
        event_id: UUID,
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)
) -> ShowEventDTO:
    event_data: Optional[dict] = await get_event_service(event_id, user, db_session)

    if event_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event with this id belonging to the current user does not exist"
        )

    return ShowEventDTO(**event_data)


@event_router.get(path="/list-of-events", response_model=List[ShowEventDTO])
async def get_list_of_events(
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)
) -> List[dict]:

    events_data: list = await get_list_of_events_service(user, db_session)

    if not events_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There are no events belonging to the current user"
        )

    return events_data


@event_router.delete(path="/")
async def delete_event(
        event_id: UUID,
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)
) -> JSONResponse:
    deleted_event_id = await delete_event_service(event_id, user, db_session)

    if deleted_event_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event with this id belonging to the current user does not exist"
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Event with id {deleted_event_id} was deleted successfully"}
    )


@event_router.patch(path="/", response_model=ShowEventDTO)
async def update_event(
        event_id: UUID,
        body: UpdateEventDTO,
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)
) -> dict:
    parameters_for_update = body.dict(exclude_none=True)
    if len(parameters_for_update) == 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one parameter must be provided"
        )

    updated_event = await update_event_service(
        event_id, parameters_for_update, user, db_session
    )

    if not updated_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event with this id belonging to the current user does not exist"
        )

    return updated_event

