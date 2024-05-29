from fastapi_mail import ConnectionConfig

SECRET_KEY: str = '2j@0lC#&8eB^k7l%oP*Vd9$LxRz!mS5wUq+4yG'
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_TOKEN_EXPIRE_DAYS: int = 30

EMAIL_CONF = ConnectionConfig(
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
