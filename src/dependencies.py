from typing import Generator

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session


async def get_db_session() -> Generator:
    """Dependence that returns async database session object
    and closes it when controller work is finished"""

    try:
        session: AsyncSession = async_session()
        yield session
    finally:
        await session.close()
