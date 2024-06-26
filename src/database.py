import os.path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker


class DatabaseSettings(BaseSettings):
    """Class representing settings related to connecting to a database"""

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    @property
    def ASYNC_DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SYNC_DATABASE_URL(self):
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def _async_engine(self):
        return create_async_engine(url=self.ASYNC_DATABASE_URL, future=True, echo=True)

    @property
    def async_session(self):
        return async_sessionmaker(self._async_engine, expire_on_commit=False)

    @property
    def _engine(self):
        return create_engine(url=self.SYNC_DATABASE_URL, echo=True)

    @property
    def session(self):
        return sessionmaker(self._engine)

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
        ),
        extra="ignore",
    )


database_settings = DatabaseSettings()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models in the project"""

    pass
