import os
from datetime import datetime, timedelta
from typing import List, Optional

from jose import jwt
from fastapi_mail import ConnectionConfig, MessageSchema, FastMail
from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr

from src.config import FRONTEND_URL, SECRET_KEY, ALGORITHM
from src.config2 import project_settings
from src.user.models import User


class EmailService:
    def __init__(self):
        self.email_conf = ConnectionConfig(
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
            instance: Optional[User] = None
    ) -> None:
        token: str = self._create_token_for_email_confirmation(
            email=email[0],
            instance=instance
        )

        message = MessageSchema(
            subject=subject,
            recipients=email,
            body=self._get_template_for_email_confirmation(
                token=token,
                template_name=template_name
            ),
            subtype="html"
        )

        fm = FastMail(self.email_conf)

        await fm.send_message(message=message)

    @staticmethod
    def _create_token_for_email_confirmation(email: str, instance: Optional[User] = None) -> str:
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
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        return token

    @staticmethod
    def _get_template_for_email_confirmation(
            token: str,
            template_name: str
    ) -> str:
        templates_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'templates')
        )
        env = Environment(loader=FileSystemLoader(templates_folder))
        template = env.get_template(template_name)
        return template.render(frontend_url=FRONTEND_URL, token=token)
