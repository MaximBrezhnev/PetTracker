from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session
from src.user.exceptions import credentials_exception
from src.user.models import User
from src.user.services.auth_services import get_email_from_token
from src.user.services.dal_services import get_user_by_email


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db_session: AsyncSession = Depends(get_db_session)) -> User:
    """Dependence that gets user from JWT token"""

    try:
        email: Optional[str] = get_email_from_token(token=token)
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user: Optional[User] = await get_user_by_email(email, db_session)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise credentials_exception

    return user

