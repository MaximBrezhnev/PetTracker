from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


class BaseDAL:
    """Base class from which all other data access
    layer services in the project are inherited"""

    def __init__(self, db_session: AsyncSession | Session):
        """Initializes a DAL service object by binding
        a session object to it"""

        self.db_session: AsyncSession | Session = db_session


DAL = TypeVar("DAL", bound=BaseDAL)


class BaseService:
    """Base class from which all other services in
    the project are inherited"""

    def __init__(self, db_session: AsyncSession, dal_class: type):
        """Initializes a service object by binding a DAL service
        with provided session object to it"""

        self.dal: DAL = dal_class(db_session)
