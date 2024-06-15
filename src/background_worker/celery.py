import os
from typing import Optional
from uuid import UUID

from celery import Celery

from src.background_worker.celery_logging import log_not_found_message, log_error
from src.background_worker.celery_services import session, get_event_from_database, update_event_when_performing_task, \
    send_email_sync, get_template_for_event, delete_completed_task, get_task_record_from_database
from src.event.models import Event


celery = Celery("background_worker")

celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:16379")  #
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:16379")  #


@celery.task(name="send_notification_email")
def send_notification_email(
        email: str,
        body: dict,
        event_id: UUID,
        task_id: UUID,
) -> None:
    db_session = session()

    try:
        task_record = get_task_record_from_database(task_id, db_session)
        if task_record is None:
            log_not_found_message(message=f"Task with id {task_id} not found")
            return

        event: Optional[Event] = get_event_from_database(event_id, db_session)
        if event is None:
            log_not_found_message(message=f"Event with id {event_id} not found")
            return

        update_event_when_performing_task(event, db_session)
        send_email_sync(
            subject="Уведомление о событии (PetTracker)",
            body=get_template_for_event(body),
            to_email=email
        )

    except Exception as err:
        log_error(err)

    finally:
        if task_record is not None:
            delete_completed_task(task_record, db_session)
        db_session.close()
