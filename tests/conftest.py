import os
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Callable
from typing import Generator
from typing import Optional
from typing import Tuple

import pytest
from celery import Celery
from celery.contrib.testing import worker
from dotenv import load_dotenv
from httpx import ASGITransport
from httpx import AsyncClient
from jose import jwt
from psycopg2 import pool
from sqlalchemy import create_engine
from sqlalchemy import Engine
from sqlalchemy import NullPool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from src.config import project_settings
from src.dependencies import get_db_session
from src.main import app
from src.pet.models import PetGenderEnum
from src.user.models import User
from src.user.services.security import create_jwt_token

load_dotenv()

TEST_DATABASE_URL: str = (
    f"postgresql+asyncpg://{os.getenv('TEST_DB_USER')}:{os.getenv('TEST_DB_PASSWORD')}@"
    f"{os.getenv('TEST_DB_HOST')}:{os.getenv('TEST_DB_PORT')}/{os.getenv('TEST_DB_NAME')}"
)

TEST_SYNC_DATABASE_URL: str = (
    f"postgresql://{os.getenv('TEST_DB_USER')}:{os.getenv('TEST_DB_PASSWORD')}@"
    f"{os.getenv('TEST_DB_HOST')}:{os.getenv('TEST_DB_PORT')}/{os.getenv('TEST_DB_NAME')}"
)
TABLES: list[str] = [
    "user",
]


@pytest.fixture(scope="session", autouse=True)
async def run_migrations() -> None:
    """Fixture that creates and runs migrations before a testing session"""

    os.system('alembic revision --autogenerate -m "test running migrations"')
    os.system("alembic upgrade head")


@pytest.fixture(scope="session")
async def configure_async_session() -> Generator[async_sessionmaker, Any, None]:
    """Fixture that configures async database session for testing session"""

    async_engine: AsyncEngine = create_async_engine(
        url=TEST_DATABASE_URL, future=True, echo=True, poolclass=NullPool
    )
    async_session: async_sessionmaker = async_sessionmaker(
        async_engine, expire_on_commit=False
    )
    yield async_session


@pytest.fixture(scope="session")
async def get_async_session(
    configure_async_session: async_sessionmaker,
) -> Generator[AsyncSession, Any, None]:
    """Fixture that creates an async session and
    closes it after the testing session"""

    session = configure_async_session()
    yield session
    await session.close()


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(get_async_session: AsyncSession) -> None:
    """Fixture that cleans tables before each test function"""

    async with get_async_session.begin():
        for table_for_cleaning in TABLES:
            await get_async_session.execute(
                text(f'TRUNCATE TABLE "{table_for_cleaning}" CASCADE')
            )


@pytest.fixture(scope="function")
async def async_client() -> Generator[AsyncClient, Any, None]:
    """Fixture that creates testing client and overrides get_db_session dependence"""

    app.dependency_overrides[get_db_session]: Callable = _get_test_db_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def _get_test_db_session() -> Generator[AsyncSession, Any, None]:
    """Dependence for testing that replaces real get_db_session dependence"""

    async_engine: AsyncEngine = create_async_engine(
        url=TEST_DATABASE_URL, future=True, echo=True
    )
    async_session: async_sessionmaker = async_sessionmaker(
        async_engine, expire_on_commit=False
    )

    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="session")
def pg_pool() -> Generator[pool.SimpleConnectionPool, Any, None]:
    """Fixture that creates a synchronous connection pool"""

    sync_pool: pool.SimpleConnectionPool = pool.SimpleConnectionPool(
        1, 10, "".join(TEST_DATABASE_URL.split("+asyncpg"))
    )
    yield sync_pool
    sync_pool.closeall()


@pytest.fixture
def get_user_from_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    """Fixture that returns function
    that is used for getting user by email"""

    def get_user_from_database_by_email(email: str) -> dict:
        connection = pg_pool.getconn()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT * FROM "user" WHERE email = %s""", (email,))
                user: Tuple = cursor.fetchone()
                return _get_user_data_dict(user)
        finally:
            pg_pool.putconn(connection)

    return get_user_from_database_by_email


def _get_user_data_dict(user: Optional[tuple]) -> Optional[dict]:
    """Function that is used by get_user_from_database fixture
    for representing data as a dictionary"""

    user_data: dict = dict()

    if user is not None:
        for field_number in range(len(user)):
            if field_number == 0:
                user_data["user_id"] = user[field_number]
            elif field_number == 1:
                user_data["username"] = user[field_number]
            elif field_number == 2:
                user_data["email"] = user[field_number]
            elif field_number == 3:
                user_data["hashed_password"] = user[field_number]
            elif field_number == 6:
                user_data["is_active"] = user[field_number]

    return user_data


@pytest.fixture
def create_user_in_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    """Fixture that returns function for creating user in database"""

    def create_user_in_database(
        user_id: str, username: str, email: str, hashed_password: str, is_active: bool
    ) -> None:
        connection = pg_pool.getconn()
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO "user" (user_id, username, email, hashed_password, is_active)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (user_id, username, email, hashed_password, is_active),
                )
                connection.commit()
            finally:
                pg_pool.putconn(connection)

    return create_user_in_database


def create_test_auth_headers_for_user(email: str) -> dict:
    access_token: str = create_jwt_token(
        email=email,
        exp_timedelta=timedelta(minutes=project_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"Authorization": f"Bearer {access_token}"}


def create_test_token_for_email_confirmation(
    email: str, instance: Optional[User] = None
) -> str:
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
        token_data, project_settings.SECRET_KEY, algorithm=project_settings.ALGORITHM
    )

    return token


@pytest.fixture
def get_pet_from_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    """Fixture that returns function for getting pet from
    database by its name"""

    def get_pet_from_database_by_name(name: str) -> dict:
        connection = pg_pool.getconn()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT * FROM pet WHERE name = %s""", (name,))
                pet: Tuple = cursor.fetchone()
                return _get_pet_data_dict(pet)
        finally:
            pg_pool.putconn(connection)

    return get_pet_from_database_by_name


def _get_pet_data_dict(pet: Optional[tuple]) -> dict:
    """Function that is used by get_pet_from_database fixture
    for representing data as a dict"""

    pet_data: dict = dict()

    if pet is not None:
        pet_data["pet_id"] = pet[0]
        pet_data["name"] = pet[1]
        pet_data["species"] = pet[2]
        pet_data["breed"] = pet[3]
        pet_data["weight"] = pet[4]
        pet_data["owner_id"] = pet[7]
        pet_data["gender"] = pet[8]

    return pet_data


@pytest.fixture
def create_pet_in_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    """Fixture that returns function for creating a pet in the database"""

    def create_pet_in_database(
        pet_id: str,
        name: str,
        species: str,
        breed: Optional[str],
        weight: int,
        gender: PetGenderEnum,
        owner_id: str,
    ) -> None:
        connection = pg_pool.getconn()
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO pet (pet_id, name, species, breed, weight, gender, owner_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """,
                    (pet_id, name, species, breed, weight, gender, owner_id),
                )
                connection.commit()
            finally:
                pg_pool.putconn(connection)

    return create_pet_in_database


@pytest.fixture
def get_event_from_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    """Fixture that returns function for getting event from
    database by its title"""

    def get_event_from_database_by_title(title: str) -> dict:
        connection = pg_pool.getconn()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT * FROM event WHERE title = %s""", (title,))
                event: Tuple = cursor.fetchone()
                return _get_event_data_dict(event)
        finally:
            pg_pool.putconn(connection)

    return get_event_from_database_by_title


def _get_event_data_dict(event: Optional[tuple]) -> dict:
    """Function that is used by get_event_from_database
    fixture for representing event data as a dict"""

    event_data: dict = dict()

    if event is not None:
        event_data["event_id"] = event[0]
        event_data["title"] = event[1]
        event_data["content"] = event[2]
        event_data["scheduled_at"] = event[3]
        event_data["pet_id"] = event[6]
        event_data["is_happened"] = event[7]

    return event_data


@pytest.fixture
def create_event_in_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    """Fixture that returns function for creating an event in the database"""

    def create_event_in_database(
        event_id: str,
        title: str,
        content: Optional[str],
        scheduled_at: datetime,
        pet_id: str,
        is_happened: bool,
    ) -> None:
        connection = pg_pool.getconn()
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO event (event_id, title, content, scheduled_at, pet_id, is_happened)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (event_id, title, content, scheduled_at, pet_id, is_happened),
                )
                connection.commit()
            finally:
                pg_pool.putconn(connection)

    return create_event_in_database


@pytest.fixture
def get_task_from_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    """Fixture that returns function for getting a task from
    the database by its event_id"""

    def get_task_from_database_by_event_id(event_id: str) -> Tuple:
        connection = pg_pool.getconn()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT * FROM task_record WHERE event_id = %s""", (event_id,)
                )
                task_record: Tuple = cursor.fetchone()
                return task_record
        finally:
            pg_pool.putconn(connection)

    return get_task_from_database_by_event_id


@pytest.fixture
def create_task_in_database(pg_pool: pool.SimpleConnectionPool) -> Callable:
    """Fixture that returns function for creating a task
    in the database"""

    def create_task_in_database(
        task_id: str,
        event_id: str,
    ) -> None:
        connection = pg_pool.getconn()
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO task_record (event_id, task_id)
                    VALUES (%s, %s);
                    """,
                    (event_id, task_id),
                )
                connection.commit()
            finally:
                pg_pool.putconn(connection)

    return create_task_in_database


@pytest.fixture(scope="session")
def celery_config() -> dict:
    """Fixture that returns the configuration for the test celery application"""

    return {
        "broker_url": "memory://",
        "result_backend": "rpc://",
        "task_always_eager": False,
    }


@pytest.fixture(scope="session")
def celery_app(celery_config: dict) -> Celery:
    """Fixture that returns the configured test celery application"""

    celery_app: Celery = Celery("test_app")
    celery_app.conf.update(celery_config)

    return celery_app


@pytest.fixture(scope="session")
def celery_worker(celery_app: Celery) -> Generator[None, Any, None]:
    """Fixture that runs test celery worker"""

    with worker.start_worker(celery_app, perform_ping_check=False):
        yield


@pytest.fixture(scope="function")
def get_sync_session() -> Generator[Session, Any, None]:
    """Fixture that creates a database session"""

    engine: Engine = create_engine(url=TEST_SYNC_DATABASE_URL, echo=True)
    session: sessionmaker = sessionmaker(engine)

    try:
        session: Session = session()
        yield session
    finally:
        session.close()
