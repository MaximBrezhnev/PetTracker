import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import UUID

from celery import Celery
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker

from src.event.models import Event


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


@celery.task(name="send_notification_email")
def send_notification_email(
        email: str,
        body: dict,
        event_id: UUID,
) -> None:
    db_session = session()
    try:
        with db_session.begin():
            result = db_session.execute(
                select(Event).filter(Event.event_id == event_id)
            )
            event = result.scalars().first()
            if event is None:
                return
            if event.is_edited:
                return

            setattr(event, "is_happened", True)
            send_email_sync(
                subject="Уведомление о событии (PetTracker)",
                body="something",
                to_email=email
            )
    except:
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

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(from_email, from_password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()
