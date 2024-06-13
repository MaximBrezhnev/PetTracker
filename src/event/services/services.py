import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

import pytz
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.event.models import Event, TaskRecord
from src.pet.models import Pet
from src.pet.schemas import PetCreationDTO
from src.user.models import User
from src.worker import send_notification_email


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

    async with db_session.begin():
        event = Event(
            title=body.title,
            content=body.content,
            scheduled_at=scheduled_at,
            pet_id=body.pet_id
        )
        db_session.add(event)
        await db_session.flush()

        task_id = uuid.uuid4()
        task_record = TaskRecord(task_id=task_id, event_id=event.event_id)
        db_session.add(task_record)
        await db_session.flush()

        query = select(Pet).filter_by(pet_id=body.pet_id)
        result = await db_session.execute(query)
        pet = result.scalars().first()

        """------------Настоящая версия-----------------------"""
        # msk_tz = pytz.timezone("Europe/Moscow")
        # scheduled_at = msk_tz.localize(scheduled_at)
        # task = send_notification_email.apply_async(
        #     (
        #         user.email,
        #         {
        #             "title": event.title,
        #             "content": event.content,
        #             "pet_id": str(event.pet_id),
        #             "year": event.scheduled_at.year,
        #             "month": event.scheduled_at.month,
        #             "day": event.scheduled_at.day,
        #             "hour": event.scheduled_at.hour,
        #             "minute": event.scheduled_at.minute
        #         },
        #         str(event.event_id),
        #         str(task_id)
        #     ),
        #     eta=scheduled_at.astimezone(pytz.utc)
        # )

    """Болванка"""
    send_notification_email(
        user.email,
        {
            "title": event.title,
            "content": event.content,
            "pet": pet.name,
            "year": event.scheduled_at.year,
            "month": event.scheduled_at.month,
            "day": event.scheduled_at.day,
            "hour": event.scheduled_at.hour,
            "minute": event.scheduled_at.minute,
        },
        str(event.event_id),
        str(task_id)
    )

    return {
        "event_id": event.event_id,
        "title": event.title,
        "content": event.content,
        "pet_id": event.pet_id,
        "year": event.scheduled_at.year,
        "month": event.scheduled_at.month,
        "day": event.scheduled_at.day,
        "hour": event.scheduled_at.hour,
        "minute": event.scheduled_at.minute,
        "is_happened": event.is_happened,
    }


async def get_event_service(
        event_id: UUID,
        user: User,
        db_session: AsyncSession
) -> Optional[Event]:
    async with db_session.begin():
        for p in user.pets:
            result = await db_session.execute(
                select(Event).filter(
                    Event.pet_id == p.pet_id,
                    Event.event_id == event_id
                )
            )
            event = result.scalars().first()
            if event is not None:
                return {
                    "event_id": event.event_id,
                    "title": event.title,
                    "content": event.content,
                    "pet_id": event.pet_id,
                    "year": event.scheduled_at.year,
                    "month": event.scheduled_at.month,
                    "day": event.scheduled_at.day,
                    "hour": event.scheduled_at.hour,
                    "minute": event.scheduled_at.minute,
                    "is_happened": event.is_happened,
                }
    return


async def get_list_of_events_service(user, db_session) -> dict:
    async with db_session.begin():
        events = []
        for p in user.pets:
            result = await db_session.execute(
                select(Event).filter(
                    Event.pet_id == p.pet_id,
                ).order_by(desc(Event.scheduled_at))
            )
            pet_events = result.scalars().all()
            if pet_events:
                events.extend(pet_events)

    for e in range(len(events)):
        event = events[e]
        events[e] = {
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

    return events


async def delete_event_service(event_id, user, db_session) -> None:
    async with db_session.begin():
        for p in user.pets:
            result = await db_session.execute(
                select(Event).filter(
                    Event.pet_id == p.pet_id,
                    Event.event_id == event_id
                )
            )
            event = result.scalars().first()
            if event is not None:
                await db_session.delete(event)
                return event.event_id
    return


async def update_event_service(
        event_id, parameters_for_update, user, db_session
) -> dict:
    async with db_session.begin():
        for p in user.pets:
            result = await db_session.execute(
                select(Event).filter(
                    Event.pet_id == p.pet_id,
                    Event.event_id == event_id
                )
            )
            event = result.scalars().first()
            if event is not None:
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

                task_id = uuid.uuid4()
                # msk_tz = pytz.timezone("Europe/Moscow")
                # scheduled_at = msk_tz.localize(scheduled_at)
                # task = send_notification_email.apply_async(
                #     (
                #         user.email,
                #         {
                #             "title": event.title,
                #             "content": event.content,
                #             "pet_id": str(event.pet_id),
                #             "year": event.scheduled_at.year,
                #             "month": event.scheduled_at.month,
                #             "day": event.scheduled_at.day,
                #             "hour": event.scheduled_at.hour,
                #             "minute": event.scheduled_at.minute
                #         },
                #         str(event.event_id),
                #         str(task_id)
                #     ),
                #     eta=scheduled_at.astimezone(pytz.utc)
                # )
                # # Посмотреть другие варианты получения объекта
                # task_records = await db_session.query(TaskRecord).\
                #     filter_by(event_id=event.event_id).all()
                # for t_r in task_records:
                #     db_session.delete(t_r)
                # task_record = TaskRecord(
                #     task_id=task.id,
                #     event_id=event.event_id
                # )
                # db_session.add(task_record)
                # await db_session.flush()

                """Болванка"""
                send_notification_email(
                    user.email,
                    {
                        "title": event.title,
                        "content": event.content,
                        "pet_id": str(event.pet_id),
                        "year": event.scheduled_at.year,
                        "month": event.scheduled_at.month,
                        "day": event.scheduled_at.day,
                        "hour": event.scheduled_at.hour,
                        "minute": event.scheduled_at.minute
                    },
                    str(event.event_id),
                    str(task_id)
                )

                return {
                    "event_id": event.event_id,
                    "title": event.title,
                    "content": event.content,
                    "pet_id": event.pet_id,
                    "year": event.scheduled_at.year,
                    "month": event.scheduled_at.month,
                    "day": event.scheduled_at.day,
                    "hours": event.scheduled_at.hour,
                    "minute": event.scheduled_at.minute,
                    "is_happened": event.is_happened,
                }

    return
