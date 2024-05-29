import os
from datetime import datetime, timedelta
from typing import List

from fastapi import (BackgroundTasks, UploadFile, File, Form,
                     Depends, HTTPException, status)  # noqa

from fastapi_mail import FastMail, MessageSchema
from jinja2 import Environment, FileSystemLoader
from jose import jwt
from pydantic import BaseModel, EmailStr

from src.config import SECRET_KEY, EMAIL_CONF
from src.user.models import User


class EmailSchema(BaseModel):
    email: List[EmailStr]


async def send_email(email: List[EmailStr], instance: User):
    token = _create_token_for_email_confirmation(instance)

    message = MessageSchema(
        subject="Письмо для подтверждения регистрации в PetTracker",
        recipients=email,
        body=_get_template_for_email_confirmation(token),
        subtype="html"
    )
    fm = FastMail(EMAIL_CONF)

    await fm.send_message(message=message)


def _create_token_for_email_confirmation(instance: User) -> str:
    current_time = datetime.utcnow()
    expiration_time = current_time + timedelta(seconds=300)

    token_data = {
        "username": instance.username,
        "exp": expiration_time,
    }

    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
    return token


def _get_template_for_email_confirmation(token: str) -> str:
    templates_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'templates')
    )
    env = Environment(loader=FileSystemLoader(templates_folder))
    template = env.get_template('confirmation_email.html')
    return template.render(token=token)

