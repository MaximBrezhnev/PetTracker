import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader

from src.config2 import project_settings


def send_email(subject: str, data: dict, to_email: str) -> None:
    server = smtplib.SMTP(project_settings.MAIL_SERVER, project_settings.MAIL_FROM)
    server.starttls()
    server.login(project_settings.MAIL_FROM, project_settings.MAIL_PASSWORD)

    message = _form_email_message(to_email, subject, data)
    server.sendmail(project_settings.MAIL_FROM, to_email, message.as_string())
    server.quit()


def _form_email_message(to_email: str, subject: str, data: dict) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg['From'] = project_settings.MAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(
        MIMEText(
            _get_template_for_event(data),
            "html"
        )
    )
    return msg


def _get_template_for_event(data: dict) -> str:
    templates_folder = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "event",
            "templates",
        )
    )

    env = Environment(loader=FileSystemLoader(templates_folder))
    template = env.get_template("event_notification.html")
    return template.render(**data)
