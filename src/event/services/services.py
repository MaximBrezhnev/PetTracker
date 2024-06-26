from datetime import datetime
from typing import List
from typing import Optional
from uuid import UUID

import pytz
from sqlalchemy.ext.asyncio import AsyncSession

from src.event.models import Event
from src.pet.models import Pet
from src.pet.services.dal import PetDAL
from src.services import BaseService
from src.user.models import User
from src.worker.celery import send_notification_email


class EventService(BaseService):
    """Service representing business logic
    used by the endpoints of event_router"""

    def __init__(self, db_session: AsyncSession, dal_class: type):
        """Initializes EventService using BaseService. Also
        creates attribute additional_dal to access to pet data"""

        super().__init__(db_session=db_session, dal_class=dal_class)
        self.additional_dal: PetDAL = PetDAL(db_session=db_session)

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
        """Creates an event in database, sends the task
        related to this event to the celery app"""

        current_user_pets: List[Pet] = await self.additional_dal.get_pets(user=user)
        if pet_id not in [p.pet_id for p in current_user_pets]:
            return

        scheduled_at = datetime(
            hour=hour, minute=minute, day=day, month=month, year=year
        )

        event: Event = await self.dal.create_event(
            title=title,
            content=content,
            pet_id=pet_id,
            scheduled_at=scheduled_at,
        )

        await self._send_task_to_celery(
            event=event,
            user=user,
            pet_id=pet_id,
            scheduled_at=scheduled_at,
            timezone=timezone,
        )
        return self._form_event_data(event=event, is_detailed=True)

    async def get_event(
        self,
        event_id: UUID,
        user: User,
    ) -> Optional[Event]:
        """Gets detailed data about an event by its id"""
        pets_of_user: List[Pet] = await self.additional_dal.get_pets(user=user)

        event: Optional[Event] = await self.dal.get_event_by_id(
            event_id=event_id, pets_of_user=pets_of_user
        )
        if event is not None:
            return self._form_event_data(event=event, is_detailed=True)

    async def get_list_of_events(self, user: User) -> List[dict]:
        """Get a list containing general information about events"""
        pets_of_user: List[Pet] = await self.additional_dal.get_pets(user=user)

        events: List[Event] = await self.dal.get_events_by_user(
            pets_of_user=pets_of_user
        )

        for e in range(len(events)):
            events[e] = self._form_event_data(event=events[e], is_detailed=False)

        return events

    async def delete_event(
        self,
        event_id: UUID,
        user: User,
    ) -> Optional[UUID]:
        """Deletes an event by its id"""
        pets_of_user: List[Pet] = await self.additional_dal.get_pets(user=user)

        event: Optional[Event] = await self.dal.get_event_by_id(
            event_id=event_id, pets_of_user=pets_of_user
        )

        if event is None:
            return

        await self.dal.delete_invalid_tasks(event=event)
        await self.dal.delete_event(event=event)

        return event.event_id

    async def update_event(
        self, event_id: UUID, parameters_for_update: dict, user: User
    ) -> dict:
        """Updates the event with the provided id. Deletes
        the old celery tasks related to this event and creates a new one"""

        pets_of_user: List[Pet] = await self.additional_dal.get_pets(user=user)

        event: Optional[Event] = await self.dal.get_event_by_id(
            event_id=event_id, pets_of_user=pets_of_user
        )

        if event is not None:
            updated_event: Event = await self.dal.update_event(
                event=event, parameters_for_update=parameters_for_update
            )

            await self.dal.delete_invalid_tasks(event=event)

            pet: Optional[Pet] = await self.additional_dal.get_pet(
                pet_id=updated_event.pet_id, user_id=user.user_id
            )
            if pet is None:
                return

            await self._send_task_to_celery(
                event=updated_event,
                user=user,
                pet_id=pet.pet_id,
                scheduled_at=updated_event.scheduled_at,
                timezone=parameters_for_update.get("timezone"),
            )
            return self._form_event_data(event=updated_event, is_detailed=True)

    @staticmethod
    def _create_task(
        scheduled_at: datetime,
        event: Event,
        user: User,
        pet: Pet,
        task_id: UUID,
        timezone: str,
    ) -> None:
        """Sends a task to the celery application"""

        msk_tz: datetime.tzinfo = pytz.timezone(timezone)
        scheduled_at: datetime = msk_tz.localize(scheduled_at)

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
                    "minute": event.scheduled_at.minute,
                },
                str(event.event_id),
                str(task_id),
            ),
            eta=scheduled_at.astimezone(pytz.utc),
        )

    @staticmethod
    def _form_event_data(event: Event, is_detailed: bool) -> dict:
        """Forms the data with the description of
        the provided event for notification email"""

        event_data: dict = {
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
            event_data.update({"content": event.content})

        return event_data

    async def _send_task_to_celery(
        self,
        event: Event,
        user: User,
        pet_id: UUID,
        scheduled_at: datetime,
        timezone: str,
    ) -> None:
        """Creates a record about a task in database and then
        sends this task to the celery application"""

        task_id: UUID = await self.dal.create_task_in_database(event=event)
        pet: Optional[Pet] = await self.additional_dal.get_pet(
            pet_id=pet_id, user_id=user.user_id
        )

        self._create_task(
            scheduled_at=scheduled_at,
            event=event,
            user=user,
            pet=pet,
            task_id=task_id,
            timezone=timezone,
        )
