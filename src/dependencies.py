from typing import Generator

from src.database import async_session


async def get_db_session() -> Generator:
    try:
        session = async_session()
        yield session
    finally:
        await session.close()
