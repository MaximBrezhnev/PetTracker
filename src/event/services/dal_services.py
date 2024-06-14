import operator
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.event.models import Event, TaskRecord
from src.pet.models import Pet
from src.user.models import User


async def create_event_in_database(
        title: str,
        content: Optional[str],
        pet_id: str,
        scheduled_at: datetime,
        db_session: AsyncSession
) -> Event:
    async with db_session.begin():
        event: Event = Event(
            title=title,
            content=content,
            scheduled_at=scheduled_at,
            pet_id=pet_id
        )
        db_session.add(event)
        await db_session.flush()

    return event


async def create_task_in_database(
        event: Event,
        db_session: AsyncSession
) -> uuid.UUID:
    task_id: uuid.UUID = uuid.uuid4()

    async with db_session.begin():
        task_record: TaskRecord = TaskRecord(task_id=task_id, event_id=event.event_id)
        db_session.add(task_record)
        await db_session.flush()

    return task_id


async def get_pet_from_database_by_id(
        pet_id: str,
        db_session: AsyncSession
) -> Pet:
    async with db_session.begin():
        result = await db_session.execute(
            select(Pet).filter_by(pet_id=pet_id)
        )

    return result.scalars().first()


async def get_event_from_database_by_id(
        event_id: uuid.UUID,
        user: User,
        db_session: AsyncSession
) -> Optional[Event]:
    async with db_session.begin():
        for p in user.pets:
            result = await db_session.execute(
                select(Event).filter_by(
                    pet_id=p.pet_id,
                    event_id=event_id
                )
            )
            return result.scalars().first()


async def get_events_from_database_by_user(
        user: User,
        db_session: AsyncSession
) -> List[Event]:
    async with db_session.begin():
        events: List = []
        for p in user.pets:
            result = await db_session.execute(
                select(Event).filter_by(pet_id=p.pet_id)
            )

            pet_events: Optional[List] = result.scalars().all()
            if pet_events:
                events.extend(pet_events)

    return sorted(
        events,
        key=operator.attrgetter("scheduled_at"),
        reverse=True
    )


async def delete_event_from_database(
        event: Event,
        db_session: AsyncSession
) -> None:
    await db_session.delete(event)


async def update_event_in_database(
        event: Event,
        parameters_for_update: dict,
        db_session: AsyncSession
) -> Event:
    async with db_session.begin():
        scheduled_at = event.scheduled_at

        for key, value in parameters_for_update.items():
            if key == "year":
                scheduled_at = scheduled_at.replace(year=value)
            elif key == "month":
                scheduled_at = scheduled_at.replace(month=value)
            elif key == "day":
                scheduled_at = scheduled_at.replace(day=value)
            elif key == "hours":
                scheduled_at = scheduled_at.replace(hour=value)
            elif key == "minutes":
                scheduled_at = scheduled_at.replace(minute=value)
            else:
                setattr(event, key, value)

        setattr(event, "scheduled_at", scheduled_at)

    return event


async def delete_invalid_tasks_from_database(
        event: Event,
        db_session: AsyncSession
) -> None:
    async with db_session.begin():
        result = await db_session.execute(
            select(TaskRecord).
            filter_by(event_id=event.event_id)
        )
        task_records = result.scalars().all()

        for t_r in task_records:
            await db_session.delete(t_r)

