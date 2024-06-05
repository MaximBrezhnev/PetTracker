from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:15432/postgres"


async_engine = create_async_engine(url=DATABASE_URL, future=True, echo=True)

async_session = async_sessionmaker(async_engine, expire_on_commit=False)





