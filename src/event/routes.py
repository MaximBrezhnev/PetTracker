from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import JSONResponse

from src.dependencies import get_current_user
from src.event.schemas import ShowEventSchema, EventCreationSchema, UpdateEventSchema
from src.event.services.services2 import EventService
from src.user.models import User
from src.event.dependencies import get_event_service


event_router = APIRouter(
    prefix="/event",
    tags=["event"]
)


@event_router.post(path="/", response_model=ShowEventSchema)
async def create_event(
        body: EventCreationSchema,
        user: User = Depends(get_current_user),
        event_service: EventService = Depends(get_event_service)
) -> ShowEventSchema:
    event_data: Optional[dict] = await event_service.create_event(
        user=user, **body.dict()
    )

    if event_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not own the pet whose event to be created"
        )

    return ShowEventSchema(**event_data)


@event_router.get(path="/", response_model=ShowEventSchema)
async def get_event(
        event_id: UUID,
        user: User = Depends(get_current_user),
        event_service: EventService = Depends(get_event_service)
) -> ShowEventSchema:
    event_data: Optional[dict] = await event_service.create_event(event_id, user)

    if event_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event with this id belonging to the current user does not exist"
        )

    return ShowEventSchema(**event_data)


@event_router.get(path="/list-of-events", response_model=List[ShowEventSchema])
async def get_list_of_events(
        user: User = Depends(get_current_user),
        event_service: EventService = Depends(get_event_service)
) -> List[dict]:

    events_data: list = await event_service.get_list_of_events(user=user)

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
        event_service: EventService = Depends(get_list_of_events)
) -> JSONResponse:
    deleted_event_id = await event_service.delete_event(event_id=event_id, user=user)

    if deleted_event_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event with this id belonging to the current user does not exist"
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Event with id {deleted_event_id} was deleted successfully"}
    )


@event_router.patch(path="/", response_model=ShowEventSchema)
async def update_event(
        event_id: UUID,
        body: UpdateEventSchema,
        user: User = Depends(get_current_user),
        event_service: EventService = Depends(get_event_service)
) -> dict:
    parameters_for_update = body.dict(exclude_none=True)
    if len(parameters_for_update) == 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one parameter must be provided"
        )

    updated_event = await event_service.update_event(
        event_id, parameters_for_update, user
    )

    if not updated_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event with this id belonging to the current user does not exist"
        )

    return updated_event
