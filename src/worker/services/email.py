import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import Template

from src.config import project_settings


def send_email(subject: str, data: dict, to_email: str) -> None:
    """Sends notification email"""

    server: smtplib.SMTP = _connect_to_smtp_server()
    message: MIMEMultipart = _form_email_message(to_email, subject, data)

    server.sendmail(project_settings.MAIL_FROM, to_email, message.as_string())
    server.quit()


def _connect_to_smtp_server() -> smtplib.SMTP:
    """Connects to a smtp server using data from project settings"""

    server: smtplib.SMTP = smtplib.SMTP(
        project_settings.MAIL_SERVER, project_settings.MAIL_PORT
    )
    server.starttls()
    server.login(project_settings.MAIL_FROM, project_settings.MAIL_PASSWORD)
    return server


def _form_email_message(to_email: str, subject: str, data: dict) -> MIMEMultipart:
    """Forms a message for notification email"""

    msg = MIMEMultipart()
    msg["From"] = project_settings.MAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(_get_template_for_event(data), "html"))
    return msg


def _get_template_for_event(data: dict) -> str:
    """Creates an html template for notification email"""

    templates_folder: str = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "event",
            "templates",
        )
    )

    env: Environment = Environment(loader=FileSystemLoader(templates_folder))
    template: Template = env.get_template("event_notification.html")
    return template.render(**data)
