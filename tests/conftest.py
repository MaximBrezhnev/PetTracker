import os
from typing import Generator, Any

import asyncpg
from psycopg2 import pool
import pytest
from asyncpg import Pool
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine

from src.dependencies import get_db_session
from src.main import app

TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:15433/postgres"
TABLES: list[str] = ["user", ]


@pytest.fixture(scope="session", autouse=True)
async def run_migrations() -> None:
    """
    Fixture that runs migrations before testing session.

    Note that os.system('alembic init migrations') has to be run only if
    you are running the tests for the first time. Also note that there will
    be an error at first start, therefore you should configure migrations manually.

    If it is not the first start, you should comment this line
    """

    # os.system('alembic init migrations')

    os.system('alembic revision --autogenerate -m "test running migrations"')
    os.system("alembic upgrade heads")


@pytest.fixture(scope="session")
async def configure_async_session():
    """Fixture that configures async database session for testing session"""

    async_engine: AsyncEngine = create_async_engine(url=TEST_DATABASE_URL, future=True, echo=True, poolclass=NullPool)
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    yield async_session


@pytest.fixture(scope="session")
async def get_async_session(configure_async_session):
    session = configure_async_session()
    yield session
    await session.close()


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(get_async_session: AsyncSession) -> None:
    """Fixture that cleans tables before each test function"""

    async with get_async_session.begin():
        for table_for_cleaning in TABLES:
            await get_async_session.execute(text(f'TRUNCATE TABLE "{table_for_cleaning}"'))


@pytest.fixture(scope="function")
async def async_client() -> Generator[AsyncClient, Any, None]:
    """Fixture that creates testing client and overrides get_db_session dependence"""

    app.dependency_overrides[get_db_session] = _get_test_db_session
    async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def _get_test_db_session() -> Generator[AsyncSession, Any, None]:
    """Dependence for testing that replaces real get_db_session dependence"""

    async_engine: AsyncEngine = create_async_engine(url=TEST_DATABASE_URL, future=True, echo=True)
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)

    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="session")
def pg_pool():
    """Fixture that creates a synchronous connection pool"""

    sync_pool = pool.SimpleConnectionPool(
        1,
        10,
        "".join(TEST_DATABASE_URL.split("+asyncpg"))
    )
    yield sync_pool
    sync_pool.closeall()


@pytest.fixture
def get_user_from_database(pg_pool):
    """Function that is used in testing for getting user by email"""

    def get_user_from_database_by_email(email: str):
        connection = pg_pool.getconn()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT * FROM "user" WHERE email = %s""", (email,))
                user = cursor.fetchone()
                return get_user_data_dict(user)
        finally:
            pg_pool.putconn(connection)

    return get_user_from_database_by_email


def get_user_data_dict(user: tuple) -> dict:
    user_data = dict()

    for field_number in range(len(user)):
        if field_number == 0:
            user_data["user_id"] = user[field_number]
        elif field_number == 1:
            user_data["username"] = user[field_number]
        elif field_number == 2:
            user_data["email"] = user[field_number]
        elif field_number == 6:
            user_data["is_active"] = user[field_number]
        elif field_number == 7:
            user_data["is_admin"] = user[field_number]

    return user_data


@pytest.fixture
def create_user_in_database(pg_pool):
    def create_user_in_database(
            user_id: str,
            username: str,
            email: str,
            hashed_password: str,
            is_active: bool,
            is_admin: bool,
    ):
        connection = pg_pool.getconn()
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO "user" (user_id, username, email, hashed_password, is_active, is_admin)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (user_id, username, email, hashed_password, is_active, is_admin),
                )
                connection.commit()
            finally:
                pg_pool.putconn(connection)

    return create_user_in_database


