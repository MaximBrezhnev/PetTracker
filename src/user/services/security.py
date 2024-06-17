from datetime import timedelta, datetime
from typing import Optional

from jose import jwt

from src.config2 import project_settings


def create_jwt_token(email: str, exp_timedelta: timedelta) -> str:
    data: dict = {"sub": email}

    expire: datetime = datetime.utcnow() + exp_timedelta
    data.update({"exp": expire})

    return jwt.encode(
        data,
        project_settings.SECRET_KEY,
        algorithm=project_settings.ALGORITHM
    )


def get_email_from_jwt_token(
        token: str
) -> Optional[str]:
    """Auth service that retrieves user's email from token payload"""

    payload: dict = jwt.decode(
        token,
        project_settings.SECRET_KEY,
        algorithms=[project_settings.ALGORITHM, ]
    )
    email: str = payload.get("sub", None)
    return email
