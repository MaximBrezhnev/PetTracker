import os

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class ProjectSettings(BaseSettings):
    """Class representing the project settings excluding
    the database settings"""

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    MAIL_CONFIRMATION_TOKEN_EXPIRE_SECONDS: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool

    PWD_SCHEMA: str
    PWD_DEPRECATED: str

    APP_TITLE: str
    API_URL_PREFIX: str
    APP_HOST: str
    APP_PORT: int
    FRONTEND_HOST: str
    FRONTEND_PORT: int

    CELERY_BROKER_HOST: str
    CELERY_RESULT_BACKEND_HOST: str
    CELERY_BROKER_PORT: int
    CELERY_RESULT_BACKEND_PORT: int

    @property
    def CELERY_BROKER_URL(self):
        return f"redis://{self.CELERY_BROKER_HOST}:{self.CELERY_BROKER_PORT}"

    @property
    def CELERY_RESULT_BACKEND_URL(self):
        return f"redis://{self.CELERY_RESULT_BACKEND_HOST}:{self.CELERY_RESULT_BACKEND_PORT}"

    @property
    def FRONTEND_URL(self):
        return f"http://{self.FRONTEND_HOST}:{self.FRONTEND_PORT}"

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
        ),
        extra="ignore",
    )


project_settings = ProjectSettings()
