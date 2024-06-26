from functools import wraps
from typing import Callable

from sqlalchemy.orm import Session

from src.database import database_settings
from src.worker.services.dal import CeleryDAL


def db_session_manager(func: Callable) -> Callable:
    """Decorator that gets a session object and provided it
    to celery task. After celery task work is finished this
    decorator closes the session"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        db_session: Session = database_settings.session()
        celery_dal: CeleryDAL = CeleryDAL(db_session=db_session)

        try:
            result: Callable = func(celery_dal, *args, **kwargs)
            return result
        finally:
            db_session.close()

    return wrapper
