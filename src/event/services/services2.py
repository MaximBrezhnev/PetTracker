from datetime import datetime
from typing import Optional
from uuid import UUID

import pytz
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.event.models import Event
from src.event.services.dal import EventDAL
from src.pet.models import Pet
from src.services import BaseService
from src.user.models import User
from src.worker.celery import send_notification_email


class EventService(BaseService):

    async def create_event(
            self,
            user: User,
            title: str,
            content: Optional[str],
            pet_id: UUID,
            hour: int,
            minute: int,
            day: int,
            month: int,
            year: int,
            timezone: str,
    ) -> Optional[dict]:
        if pet_id not in [p.pet_id for p in user.pets]:
            return

        scheduled_at = datetime(
            hour=hour,
            minute=minute,
            day=day,
            month=month,
            year=year
        )

        event: Event = await self.dal.create_event(
            title=title,
            content=content,
            pet_id=pet_id,
            scheduled_at=scheduled_at,
        )

        pet: Pet = await self.dal.get_pet_by_id(pet_id=pet_id)
        if pet is None:
            return

        await self._send_task_to_celery(
            event, user, pet, scheduled_at, timezone
        )
        return self._form_event_data(event=event, is_detailed=True)

    async def get_event(
            self,
            event_id: UUID,
            user: User,
    ) -> Optional[Event]:
        event: Optional[Event] = self.dal.get_event_by_id(
            event_id=event_id,
            user=user,
        )
        if event is not None:
            return self._form_event_data(event=event, is_detailed=True)

    async def get_list_of_events(self, user: User) -> dict:
        events: List[Event] = await self.dal.get_events_by_user(user=user)

        for e in range(len(events)):
            events[e] = self._form_event_data(
                event=events[e], is_detailed=False
            )

        return events

    async def delete_event(
            self,
            event_id: UUID,
            user: User,
    ) -> Optional[UUID]:
        event: Optional[Event] = await self.dal.get_event_by_id(
            event_id=event_id, user=user
        )

        if event is not None:
            await self.dal.delete_event(event=event)
            return event.event_id

    async def update_event(
            self,
            event_id: UUID,
            parameters_for_update: dict,
            user: User
    ) -> dict:
        event: Optional[Event] = await self.dal.get_event_by_id(
            event_id=event_id,
            user=user
        )

        if event is not None:
            updated_event: Event = await self.dal.update_event(
                event=event,
                parameters_for_update=parameters_for_update
            )

            await self.dal.delete_invalid_tasks_from_database(event=event)

            pet: Pet = await self.dal.get_pet_by_id(pet_id=updated_event.pet_id)
            if pet is None:
                return

            await self._send_task_to_celery(
                updated_event,
                user,
                pet,
                updated_event.scheduled_at,
                parameters_for_update.get("timezone")
            )
            return self._form_event_data(event=updated_event, is_detailed=True)

    @staticmethod
    def _create_task(
            scheduled_at: datetime,
            event: Event,
            user: User,
            pet: Pet,
            task_id: UUID,
            timezone: str
    ) -> None:
        msk_tz = pytz.timezone(timezone)
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

    @staticmethod
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
            self,
            event: Event,
            user: User,
            pet: Pet,
            scheduled_at: datetime,
            timezone: str
    ) -> None:
        task_id: UUID = await self.dal.create_task_in_database(event=event)

        self._create_task(
            scheduled_at=scheduled_at,
            event=event,
            user=user,
            pet=pet,
            task_id=task_id,
            timezone=timezone
        )
