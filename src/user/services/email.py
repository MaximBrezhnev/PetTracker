import os
from datetime import datetime
from datetime import timedelta
from typing import List
from typing import Optional

from fastapi_mail import ConnectionConfig
from fastapi_mail import FastMail
from fastapi_mail import MessageSchema
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import Template
from jose import jwt
from pydantic import EmailStr

from src.config import project_settings
from src.user.models import User


class EmailService:
    """Service that enables to send emails asynchronously"""

    def __init__(self):
        """Initializes EmailService by creating
        an email sending configuration"""

        self.email_conf: ConnectionConfig = ConnectionConfig(
            MAIL_USERNAME=project_settings.MAIL_USERNAME,
            MAIL_PASSWORD=project_settings.MAIL_PASSWORD,
            MAIL_FROM=project_settings.MAIL_FROM,
            MAIL_PORT=project_settings.MAIL_PORT,
            MAIL_SERVER=project_settings.MAIL_SERVER,
            MAIL_STARTTLS=project_settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=project_settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=project_settings.USE_CREDENTIALS,
            VALIDATE_CERTS=project_settings.VALIDATE_CERTS,
        )

    async def send_email(
        self,
        email: List[EmailStr],
        subject: str,
        template_name: str,
        instance: Optional[User] = None,
    ) -> None:
        """Sends email with email confirmation token"""

        token: str = self._create_token_for_email_confirmation(
            email=email[0], instance=instance
        )

        message: MessageSchema = MessageSchema(
            subject=subject,
            recipients=email,
            body=self._get_template_for_email_confirmation(
                token=token, template_name=template_name
            ),
            subtype="html",
        )

        fm: FastMail = FastMail(self.email_conf)

        await fm.send_message(message=message)

    @staticmethod
    def _create_token_for_email_confirmation(
        email: str, instance: Optional[User] = None
    ) -> str:
        """Creates email confirmation token using jwt module"""

        current_time: datetime = datetime.utcnow()
        expiration_time: datetime = current_time + timedelta(
            seconds=project_settings.MAIL_CONFIRMATION_TOKEN_EXPIRE_SECONDS
        )

        token_data: dict = {
            "email": email,
            "exp": expiration_time,
        }

        if instance is not None:
            if email != instance.email:
                token_data.update({"current_user_id": str(instance.user_id)})

        token: str = jwt.encode(
            token_data,
            project_settings.SECRET_KEY,
            algorithm=project_settings.ALGORITHM,
        )

        return token

    @staticmethod
    def _get_template_for_email_confirmation(token: str, template_name: str) -> str:
        """Gets and renders template for email confirmation"""

        templates_folder: str = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "templates")
        )
        env: Environment = Environment(loader=FileSystemLoader(templates_folder))
        template: Template = env.get_template(template_name)
        return template.render(frontend_url=project_settings.FRONTEND_URL, token=token)
