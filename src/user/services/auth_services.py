from datetime import timedelta, datetime
from typing import Optional

from jose import jwt

from src.config import SECRET_KEY, ALGORITHM


def check_password(hashed_password: str, password: str) -> bool:
    return hashed_password == password


def create_jwt_token(email: str, exp_timedelta: timedelta) -> str:
    data: dict = {"sub": email}

    expire: datetime = datetime.utcnow() + exp_timedelta
    data.update({"exp": expire})

    return jwt.encode(
        data, SECRET_KEY, algorithm=ALGORITHM
    )


def get_email_from_token(token: str) -> Optional[str]:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email: str = payload.get("sub", None)
    return email

