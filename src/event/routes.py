from typing import List
from typing import Optional
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from starlette.responses import JSONResponse

from src.dependencies import get_current_user
from src.event.dependencies import get_event_service
from src.event.models import Event
from src.event.schemas import EventCreationSchema
from src.event.schemas import ShowEventSchema
from src.event.schemas import UpdateEventSchema
from src.event.services.services import EventService
from src.user.models import User


event_router: APIRouter = APIRouter(prefix="/event", tags=["event"])


@event_router.post(path="/", response_model=ShowEventSchema)
async def create_event(
    body: EventCreationSchema,
    user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> ShowEventSchema:
    """Endpoint that creates a new event related to the provided pet"""

    event_data: Optional[dict] = await event_service.create_event(
        user=user, **body.model_dump()
    )

    if event_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not own the pet whose event to be created",
        )

    return ShowEventSchema(**event_data)


@event_router.get(path="/", response_model=ShowEventSchema)
async def get_event(
    event_id: UUID,
    user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> ShowEventSchema:
    """Endpoint that gets an event by its id"""

    event_data: Optional[dict] = await event_service.get_event(event_id, user)

    if event_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event with this id belonging to the current user does not exist",
        )

    return ShowEventSchema(**event_data)


@event_router.get(path="/list-of-events", response_model=List[ShowEventSchema])
async def get_list_of_events(
    user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> List[dict]:
    """Endpoint that gets a list of events created by the current user"""

    events_data: List[dict] = await event_service.get_list_of_events(user=user)

    if not events_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no events belonging to the current user",
        )

    return events_data


@event_router.delete(path="/")
async def delete_event(
    event_id: UUID,
    user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> JSONResponse:
    """Endpoint that deletes event by its id"""

    deleted_event_id: Optional[UUID] = await event_service.delete_event(
        event_id=event_id, user=user
    )

    if deleted_event_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event with this id belonging to the current user does not exist",
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Event with id {deleted_event_id} was deleted successfully"
        },
    )


@event_router.patch(path="/", response_model=ShowEventSchema)
async def update_event(
    event_id: UUID,
    body: UpdateEventSchema,
    user: User = Depends(get_current_user),
    event_service: EventService = Depends(get_event_service),
) -> dict:
    """Endpoint that updates the event with the provided id"""

    parameters_for_update: dict = body.model_dump(exclude_none=True)
    if len(parameters_for_update) <= 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one parameter must be provided",
        )

    updated_event: Optional[Event] = await event_service.update_event(
        event_id, parameters_for_update, user
    )

    if not updated_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event with this id belonging to the current user does not exist",
        )

    return updated_event
