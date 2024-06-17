from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.event.models import TaskRecord, Event
from src.services import BaseDAL


class CeleryDAL(BaseDAL):
    def get_task_record(self, task_id: UUID) -> Optional[TaskRecord]:
        result = self.db_session.execute(
            select(TaskRecord).filter_by(task_id=task_id)
        )
        return result.scalars().first()

    def get_event(self, event_id: UUID) -> Optional[Event]:
        result = self.db_session.execute(
            select(Event).filter_by(event_id=event_id)
        )
        return result.scalars().first()

    def update_event_when_performing_task(self, event: Event) -> None:
        with self.db_session:
            setattr(event, "is_happened", True)

    def delete_completed_task(self, task_record: TaskRecord):
        self.db_session.delete(task_record)

