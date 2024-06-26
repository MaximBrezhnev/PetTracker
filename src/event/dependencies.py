from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session
from src.event.services.dal import EventDAL
from src.event.services.services import EventService


def get_event_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> EventService:
    """Dependence that creates EventService object using
    session object from get_db_session dependence and EventDAL service"""

    return EventService(db_session=db_session, dal_class=EventDAL)
