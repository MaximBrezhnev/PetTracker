from typing import Any
from typing import Generator
from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import Result
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import database_settings
from src.exceptions import credentials_exception
from src.user.models import User
from src.user.services import security


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/auth/login")


async def get_db_session() -> Generator[AsyncSession, Any, None]:
    """Dependence that returns async database session object
    and closes it when controller work is finished"""

    try:
        session: AsyncSession = database_settings.async_session()
        yield session
    finally:
        await session.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_session: AsyncSession = Depends(get_db_session),
) -> User:
    """Dependence that gets user from JWT token"""

    try:
        email: Optional[str] = security.get_email_from_jwt_token(token=token)
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user: Optional[User] = await _get_user_by_email_from_database(
        email=email, db_session=db_session
    )
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise credentials_exception

    return user


async def _get_user_by_email_from_database(
    email: str, db_session: AsyncSession
) -> Optional[User]:
    """Function used by get_current_user dependence for
    getting a user from database by email from a token"""

    async with db_session:
        result: Result = await db_session.execute(select(User).filter_by(email=email))
        return result.scalars().first()
