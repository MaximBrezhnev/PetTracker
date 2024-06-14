from typing import Optional
from uuid import UUID

from src.background_worker.celery_config import celery
from src.background_worker.celery_logging import log_event_not_found, log_error
from src.background_worker.celery_services import get_event_from_database, update_event_when_performing_task, \
    delete_completed_task, send_email_sync, get_template_for_event, session
from src.event.models import Event


@celery.task(name="send_notification_email")
def send_notification_email(
        email: str,
        body: dict,
        event_id: UUID,
        task_id: UUID,
) -> None:
    db_session = session()

    try:
        event: Optional[Event] = get_event_from_database(event_id, db_session)

        if event is None:
            log_event_not_found(event_id)
            return

        update_event_when_performing_task(event, db_session)
        send_email_sync(
            subject="Уведомление о событии (PetTracker)",
            body=get_template_for_event(body),
            to_email=email
        )

        delete_completed_task(task_id, db_session)

    except Exception as err:
        log_error(err)
        return

    finally:
        db_session.close()
