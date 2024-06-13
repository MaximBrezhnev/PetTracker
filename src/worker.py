import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID

from celery import Celery
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker

from src.event.models import Event, TaskRecord

import logging
from datetime import datetime

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:16379")  #
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:16379")  #

celery.conf.update(
    timezone="Europe/Moscow",
    enable_utc=False,
)

sync_engine = create_engine(
    url="postgresql+psycopg://postgres:postgres@localhost:15432/postgres",  #
    echo=False,
)
session = sessionmaker(sync_engine)

# Объявление логирования
logger = logging.getLogger('worker_logger')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('worker.log')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def log_event_not_found(identifier):
    message = f"Событие с указанным идентификатором не найдено: {identifier}"
    logger.info(message)


def log_error(error_message):
    logger.error(error_message)


@celery.task(name="send_notification_email")
def send_notification_email(
        email: str,
        body: dict,
        event_id: UUID,
        task_id: UUID,
) -> None:
    db_session = session()
    try:
        with db_session.begin():
            result = db_session.execute(
                select(Event).filter(Event.event_id == event_id)
            )
            event = result.scalars().first()
            if event is None:
                log_event_not_found(event_id)
                return

            setattr(event, "is_happened", True)
            send_email_sync(
                subject="Уведомление о событии (PetTracker)",
                body=get_template_for_event(body),
                to_email=email
            )

            task_record = db_session.query(TaskRecord).\
                filter_by(task_id=task_id).first()
            db_session.delete(task_record)
    except Exception as err:
        log_error(err)
        return
    finally:
        db_session.close()


def send_email_sync(subject: str, body: str, to_email: str):
    from_email = "max.b04.03@mail.ru"
    from_password = "vgg0wQQcx6dbWZ5u2adc"
    smtp_server = "smtp.mail.ru"
    smtp_port = 2525

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(from_email, from_password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()


def get_template_for_event(data: dict) -> str:
    templates_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'event', 'templates')
    )
    env = Environment(loader=FileSystemLoader(templates_folder))
    template = env.get_template("event_notification.html")
    return template.render(**data)
