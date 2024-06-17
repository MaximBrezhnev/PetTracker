import logging
import os
from typing import Optional
from uuid import UUID

from celery import Celery

from src.config2 import project_settings
from src.event.models import Event
from src.worker.database import db_session_manager
from src.worker.logging import CeleryLogger
from src.worker.services.dal import CeleryDAL
from src.worker.services.email import send_email

celery = Celery("worker")
celery.conf.broker_url = project_settings.CELERY_BROKER_URL
celery.conf.result_backend = project_settings.CELERY_RESULT_BACKEND_URL


log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
logger = CeleryLogger(
    logger_name="celery_logger",
    level=logging.DEBUG,
    log_file=os.path.join(log_dir, "worker.log")
)


@celery.task(name="send_notification_email")
@db_session_manager
def send_notification_email(
        celery_dal: CeleryDAL,
        email: str,
        body: dict,
        event_id: UUID,
        task_id: UUID,
) -> None:
    try:
        task_record = celery_dal.get_task_record(task_id)
        if task_record is None:
            logger.log_not_found_message(
                message=f"Task with id {task_id} not found"
            )
            return

        event: Optional[Event] = celery_dal.get_event(event_id)
        if event is None:
            logger.log_not_found_message(
                message=f"Event with id {event_id} not found"
            )
            return

        celery_dal.update_event_when_performing_task(event)

        send_email(
            subject="Уведомление о событии (PetTracker)",
            data=body,
            to_email=email
        )

    except Exception as err:
        logger.log_error(err)
        return

    finally:
        if task_record is not None:
            celery_dal.delete_completed_task(task_record)
