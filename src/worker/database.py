from functools import wraps

from src.config2 import project_settings
from src.worker.services.dal import CeleryDAL


def db_session_manager(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        db_session = project_settings.session()
        celery_dal = CeleryDAL(db_session=db_session)

        try:
            result = func(celery_dal, *args, **kwargs)
            return result
        finally:
            db_session.close()

    return wrapper
