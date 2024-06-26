import operator
import uuid
from datetime import datetime
from typing import List
from typing import Optional

from sqlalchemy import select

from src.event.models import Event
from src.event.models import TaskRecord
from src.pet.models import Pet
from src.services import BaseDAL


class EventDAL(BaseDAL):
    """Data access layer service that enables to work with the data
    related to the events"""

    async def create_event(
        self,
        title: str,
        content: Optional[str],
        pet_id: str,
        scheduled_at: datetime,
    ) -> Event:
        """Creates event in database"""

        async with self.db_session.begin():
            event: Event = Event(
                title=title, content=content, scheduled_at=scheduled_at, pet_id=pet_id
            )
            self.db_session.add(event)
            await self.db_session.flush()

            return event

    async def create_task_in_database(self, event: Event) -> uuid.UUID:
        """Creates the celery task
        associated with the provided event in database"""

        async with self.db_session.begin():
            task_id: uuid.UUID = uuid.uuid4()

            task_record: TaskRecord = TaskRecord(
                task_id=task_id, event_id=event.event_id
            )
            self.db_session.add(task_record)
            await self.db_session.flush()

            return task_id

    async def get_event_by_id(
        self, event_id: uuid.UUID, pets_of_user: List[Pet]
    ) -> Optional[Event]:
        """Gets an event from database by its id"""

        async with self.db_session.begin():
            for p in pets_of_user:
                result = await self.db_session.execute(
                    select(Event).filter_by(pet_id=p.pet_id, event_id=event_id)
                )
                event: Optional[Event] = result.scalars().first()
                if event is not None:
                    return event

    async def get_events_by_user(self, pets_of_user: List[Pet]) -> List[Event]:
        """Gets a list of events from database by user
        ordered by parameter "scheduled_at" """

        async with self.db_session.begin():
            events: List = []

            for p in pets_of_user:
                result = await self.db_session.execute(
                    select(Event).filter_by(pet_id=p.pet_id)
                )

                pet_events: Optional[List] = result.scalars().all()
                if pet_events:
                    events.extend(pet_events)

        return sorted(events, key=operator.attrgetter("scheduled_at"), reverse=True)

    async def delete_event(self, event: Event) -> None:
        """Deletes the provided event from database"""

        async with self.db_session.begin():
            await self.db_session.delete(event)

    async def update_event(
        self,
        event: Event,
        parameters_for_update: dict,
    ) -> Event:
        """Updates the provided event using the provided data"""

        async with self.db_session.begin():
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

    async def delete_invalid_tasks(self, event: Event) -> None:
        """Deletes invalid celery tasks related to
        the provided event from database"""

        async with self.db_session.begin():
            result = await self.db_session.execute(
                select(TaskRecord).filter_by(event_id=event.event_id)
            )
            task_records = result.scalars().all()

            for t_r in task_records:
                await self.db_session.delete(t_r)
