import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.event.models import Event
from src.event.services.dal_services import create_event_in_database, create_task_in_database, \
    get_pet_from_database_by_id, get_event_from_database_by_id, get_events_from_database_by_user, \
    delete_event_from_database, update_event_in_database, delete_invalid_tasks_from_database
from src.pet.models import Pet
from src.pet.schemas import PetCreationDTO
from src.user.models import User
from src.background_worker.celery_tasks import send_notification_email


async def create_event_service(
        body: PetCreationDTO,
        user: User,
        db_session: AsyncSession,
) -> Optional[dict]:
    if body.pet_id not in [p.pet_id for p in user.pets]:
        return

    scheduled_at = datetime(
        hour=body.hour,
        minute=body.minute,
        day=body.day,
        month=body.month,
        year=body.year
    )

    event: Event = await create_event_in_database(
        title=body.title,
        content=body.content,
        pet_id=body.pet_id,
        scheduled_at=scheduled_at,
        db_session=db_session
    )

    pet: Pet = await get_pet_from_database_by_id(
        pet_id=body.pet_id, db_session=db_session
    )
    if pet is None:
        return

    await _send_task_to_celery(event, user, pet, scheduled_at, db_session)
    return _form_event_data(event=event, is_detailed=True)


async def get_event_service(
        event_id: UUID,
        user: User,
        db_session: AsyncSession
) -> Optional[Event]:
    event: Optional[Event] = get_event_from_database_by_id(
        event_id=event_id,
        user=user,
        db_session=db_session
    )
    if event is not None:
        return _form_event_data(event=event, is_detailed=True)


async def get_list_of_events_service(
        user: User,
        db_session: AsyncSession
) -> dict:
    events: List[Event] = await get_events_from_database_by_user(
        user=user, db_session=db_session
    )

    for e in range(len(events)):
        events[e] = _form_event_data(
            event=events[e], is_detailed=False
        )

    return events


async def delete_event_service(
        event_id: UUID,
        user: User,
        db_session: AsyncSession
) -> Optional[UUID]:
    event: Optional[Event] = await get_event_from_database_by_id(
        event_id=event_id, user=user, db_session=db_session
    )

    if event is not None:
        await delete_event_from_database(event, db_session)
        return event.event_id


async def update_event_service(
        event_id: UUID,
        parameters_for_update: dict,
        user: User,
        db_session: AsyncSession
) -> dict:
    event: Optional[Event] = await get_event_from_database_by_id(
        event_id=event_id, user=user, db_session=db_session
    )

    if event is not None:
        updated_event: Event = await update_event_in_database(
            event=event, parameters_for_update=parameters_for_update, db_session=db_session
        )

        await delete_invalid_tasks_from_database(event=event, db_session=db_session)

        pet: Pet = await get_pet_from_database_by_id(
            pet_id=updated_event.pet_id, db_session=db_session
        )
        if pet is None:
            return

        await _send_task_to_celery(updated_event, user, pet, updated_event.scheduled_at, db_session)
        return _form_event_data(event=updated_event, is_detailed=True)


def _create_task(
        scheduled_at: datetime,
        event: Event,
        user: User,
        pet: Pet,
        task_id: UUID
) -> None:
    msk_tz = pytz.timezone("Europe/Moscow")
    scheduled_at = msk_tz.localize(scheduled_at)

    send_notification_email.apply_async(
        (
            user.email,
            {
                "title": event.title,
                "content": event.content,
                "pet": pet.name,
                "year": event.scheduled_at.year,
                "month": event.scheduled_at.month,
                "day": event.scheduled_at.day,
                "hour": event.scheduled_at.hour,
                "minute": event.scheduled_at.minute
            },
            str(event.event_id),
            str(task_id)
        ),
        eta=scheduled_at.astimezone(pytz.utc)
    )


def _form_event_data(
        event: Event,
        is_detailed: bool
) -> dict:
    event_data = {
        "event_id": event.event_id,
        "title": event.title,
        "pet_id": event.pet_id,
        "year": event.scheduled_at.year,
        "month": event.scheduled_at.month,
        "day": event.scheduled_at.day,
        "hour": event.scheduled_at.hour,
        "minute": event.scheduled_at.minute,
        "is_happened": event.is_happened,
    }

    if is_detailed:
        event_data.update(
            {"content": event.content}
        )

    return event_data


async def _send_task_to_celery(
        event: Event,
        user: User,
        pet: Pet,
        scheduled_at: datetime,
        db_session: AsyncSession
) -> None:
    task_id: UUID = await create_task_in_database(
        event=event, db_session=db_session
    )

    _create_task(
        scheduled_at=scheduled_at,
        event=event,
        user=user,
        pet=pet,
        task_id=task_id
    )

