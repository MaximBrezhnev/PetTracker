import operator
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.event.models import Event, TaskRecord
from src.pet.models import Pet
from src.services import BaseDAL
from src.user.models import User


class EventDAL(BaseDAL):
    async def create_event(
            self,
            title: str,
            content: Optional[str],
            pet_id: str,
            scheduled_at: datetime,
    ) -> Event:
        event: Event = Event(
            title=title,
            content=content,
            scheduled_at=scheduled_at,
            pet_id=pet_id
        )
        self.db_session.add(event)
        await self.db_session.flush()

        return event

    async def create_task_in_database(self, event: Event) -> uuid.UUID:
        task_id: uuid.UUID = uuid.uuid4()

        task_record: TaskRecord = TaskRecord(task_id=task_id, event_id=event.event_id)
        self.db_session.add(task_record)
        await self.db_session.flush()

        return task_id

    async def get_pet_by_id(
            self,
            pet_id: str,
    ) -> Pet:
        result = await self.db_session.execute(
            select(Pet).filter_by(pet_id=pet_id)
        )

        return result.scalars().first()

    async def get_event_by_id(
            self,
            event_id: uuid.UUID,
            user: User,
    ) -> Optional[Event]:
        for p in user.pets:
            result = await self.db_session.execute(
                select(Event).filter_by(
                    pet_id=p.pet_id,
                    event_id=event_id
                )
            )
            return result.scalars().first()

    async def get_events_by_user(self, user: User) -> List[Event]:
        events: List = []
        for p in user.pets:
            result = await self.db_session.execute(
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

    async def delete_event(self, event: Event) -> None:
        await self.db_session.delete(event)

    async def update_event(
            self,
            event: Event,
            parameters_for_update: dict,
    ) -> Event:
        async with self.db_session:
            scheduled_at = event.scheduled_at

            for key, value in parameters_for_update.items():
                if key == "year":
                    scheduled_at = scheduled_at.replace(year=value)
                elif key == "month":
                    scheduled_at = scheduled_at.replace(month=value)
                elif key == "day":
                    scheduled_at = scheduled_at.replace(day=value)
                elif key == "hour":
                    scheduled_at = scheduled_at.replace(hour=value)
                elif key == "minute":
                    scheduled_at = scheduled_at.replace(minute=value)
                else:
                    setattr(event, key, value)

            setattr(event, "scheduled_at", scheduled_at)

        return event

    async def delete_invalid_tasks_from_database(self, event: Event) -> None:
        result = await self.db_session.execute(
            select(TaskRecord).filter_by(event_id=event.event_id)
        )
        task_records = result.scalars().all()

        for t_r in task_records:
            await self.db_session.delete(t_r)

