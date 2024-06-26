from typing import Optional
from uuid import UUID

from sqlalchemy import Result
from sqlalchemy import select

from src.event.models import Event
from src.event.models import TaskRecord
from src.services import BaseDAL


class CeleryDAL(BaseDAL):
    """Class representing DAL service that enables
    celery app to work with database"""

    def get_task_record_by_id(self, task_id: UUID) -> Optional[TaskRecord]:
        """Gets task record from database by its identifier"""

        with self.db_session.begin():
            result: Result = self.db_session.execute(
                select(TaskRecord).filter_by(task_id=task_id)
            )
            return result.scalars().first()

    def get_event_by_id(self, event_id: UUID) -> Optional[Event]:
        """Gets event from database by its identifier"""

        with self.db_session.begin():
            result = self.db_session.execute(select(Event).filter_by(event_id=event_id))
            return result.scalars().first()

    def update_event_when_performing_task(self, event: Event) -> None:
        """Sets the parameter is_happened of the event to True
        after the task is completed"""

        with self.db_session.begin():
            setattr(event, "is_happened", True)

    def delete_completed_task(self, task_record: TaskRecord):
        """Deletes completed task from database after it is completed"""

        with self.db_session.begin():
            self.db_session.delete(task_record)
