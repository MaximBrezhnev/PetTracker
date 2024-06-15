import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from uuid import UUID

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from src.event.models import Event, TaskRecord


sync_engine = create_engine(
    url="postgresql+psycopg://postgres:postgres@db:5432/postgres",  #
    echo=False,
)
session = sessionmaker(sync_engine)


def get_task_record_from_database(
        task_id: str,
        db_session: Session
) -> Optional[TaskRecord]:
    with db_session.begin():
        result = db_session.execute(
            select(TaskRecord).filter_by(task_id=task_id)
        )

        return result.scalars().first()


def get_event_from_database(event_id: UUID, db_session: Session) -> Optional[Event]:
    with db_session.begin():
        result = db_session.execute(
            select(Event).filter_by(event_id=event_id)
        )

    return result.scalars().first()


def update_event_when_performing_task(event: Event, db_session: Session) -> None:
    with db_session.begin():
        setattr(event, "is_happened", True)


def send_email_sync(subject: str, body: str, to_email: str) -> None:
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
        os.path.join(os.path.dirname(__file__), '../event', 'templates')
    )
    env = Environment(loader=FileSystemLoader(templates_folder))
    template = env.get_template("event_notification.html")
    return template.render(**data)


def delete_completed_task(
        task_record: TaskRecord,
        db_session: Session
) -> None:
    with db_session.begin():
        db_session.delete(task_record)
