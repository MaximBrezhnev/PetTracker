import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi_mail import FastMail, MessageSchema
from jinja2 import Environment, FileSystemLoader
from jose import jwt
from pydantic import EmailStr

from src.config import SECRET_KEY, EMAIL_CONF, FRONTEND_URL, ALGORITHM
from src.user.models import User


async def send_email(
        email: List[EmailStr],
        subject: str,
        template_name: str,
        instance: Optional[User] = None) -> None:
    token = _create_token_for_email_confirmation(email[0], instance)

    message = MessageSchema(
        subject=subject,
        recipients=email,
        body=_get_template_for_email_confirmation(token, template_name),
        subtype="html"
    )
    fm = FastMail(EMAIL_CONF)

    await fm.send_message(message=message)


def _create_token_for_email_confirmation(email: str, instance: Optional[User] = None) -> str:
    current_time: datetime = datetime.utcnow()
    expiration_time: datetime = current_time + timedelta(seconds=300)

    token_data: dict = {
        "email": email,
        "exp": expiration_time,
    }

    if instance is not None:
        if email != instance.email:
            token_data.update({"current_user_id": str(instance.user_id)})

    token: str = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return token


def _get_template_for_email_confirmation(token: str, template_name: str) -> str:
    templates_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'templates')
    )
    env = Environment(loader=FileSystemLoader(templates_folder))
    template = env.get_template(template_name)
    return template.render(frontend_url=FRONTEND_URL, token=token)

