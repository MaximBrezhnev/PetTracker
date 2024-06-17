from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class BaseService:
    def __init__(self, db_session: AsyncSession, dal_class):
        self.dal = dal_class(db_session)


class BaseDAL:
    def __init__(self, db_session: AsyncSession | Session):
        self.db_session = db_session
