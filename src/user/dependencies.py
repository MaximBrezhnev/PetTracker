from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session
from src.user.services.dal import UserDAL
from src.user.services.services2 import UserService


def get_user_service(
        db_session: AsyncSession = Depends(get_db_session)
) -> UserService:

    return UserService(db_session=db_session, dal_class=UserDAL)
