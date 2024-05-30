from datetime import timedelta, datetime
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from src.config import SECRET_KEY, ALGORITHM


pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def check_password(hashed_password: str, password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_jwt_token(email: str, exp_timedelta: timedelta) -> str:
    data: dict = {"sub": email}

    expire: datetime = datetime.utcnow() + exp_timedelta
    data.update({"exp": expire})

    return jwt.encode(
        data, SECRET_KEY, algorithm=ALGORITHM
    )


def get_email_from_token(token: str) -> Optional[str]:
    payload: dict = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email: str = payload.get("sub", None)
    return email

