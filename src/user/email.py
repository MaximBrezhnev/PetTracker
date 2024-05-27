from datetime import datetime, timedelta
from typing import List

from fastapi import (BackgroundTasks, UploadFile, File, Form,
                     Depends, HTTPException, status)  # noqa


from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jose import jwt
from pydantic import BaseModel, EmailStr

from src.user.models import User


SECRET_KEY = '2j@0lC#&8eB^k7l%oP*Vd9$LxRz!mS5wUq+4yG'


conf = ConnectionConfig(
    MAIL_USERNAME="max.b04.03@mail.ru",
    MAIL_PASSWORD="vgg0wQQcx6dbWZ5u2adc",
    MAIL_FROM="max.b04.03@mail.ru",
    MAIL_PORT=2525,
    MAIL_SERVER="smtp.mail.ru",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


class EmailSchema(BaseModel):
    email: List[EmailStr]


async def send_email(email: List[EmailStr], instance: User):
    current_time = datetime.utcnow()
    expiration_time = current_time + timedelta(seconds=30)

    token_data = {
        "user_id": str(instance.user_id),
        "username": instance.username,
        "exp": expiration_time,
    }

    token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")

    template = f"""
            <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
            <div style=" display: flex; align-items: center; justify-content: center; flex-direction: column;">
                <h3> Account Verification </h3>
                <br>
                <p>Thanks for choosing our site, please 
                click on the link below to verify your account</p> 

                <a style="margin-top:1rem; padding: 1rem; border-radius: 0.5rem; font-size: 1rem; text-decoration: none; background: #0275d8; color: white;"
                 href="http://localhost:8000/api/v1/user/verification/?token={token}">
                    Verify your email
                <a>

                <p style="margin-top:1rem;">If you did not register for PetTracker, 
                please kindly ignore this email and nothing will happen. Thanks<p>
            </div>
        </body>
        </html>
    """

    message = MessageSchema(
        subject="PetTracker Account Verification Email",
        recipients=email,
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    # Здесь будет нормальная обработка ошибок, связанных с smtp
    try:
        await fm.send_message(message=message)
    except:
        pass
