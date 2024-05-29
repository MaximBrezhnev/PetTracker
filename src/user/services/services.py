from datetime import timedelta
from typing import Optional
from uuid import UUID

from jose import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from src.user.models import User
from src.user.schemas import CreateUserDTO
from src.user.services.auth_services import check_password, create_jwt_token, get_email_from_token
from src.user.services.dal_services import get_user_by_email, update_username_and_password, create_new_user, \
    get_user_by_username, update_user_upon_verification, get_user_by_user_id, update_user, delete_user
from src.user.services.email_servcies import send_email


async def create_user_service(body: CreateUserDTO, db_session: AsyncSession) -> None:
    user = await get_user_by_email(body.email, db_session)

    if user is not None:
        if user.is_active:
            raise ValueError("User already exists")
        await update_username_and_password(body.username, body.password1, user, db_session)

    else:
        user = await create_new_user(body.username, body.email, body.password1, db_session)

    await send_email(email=[user.email, ], instance=user)


async def verify_email_service(token: str, db_session: AsyncSession) -> None:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = await get_user_by_username(payload.get("username", None), db_session)

    if user is None:
        raise ValueError("User does not exist")

    await update_user_upon_verification(user, db_session)


async def get_user_service(user_id: UUID, db_session: AsyncSession) -> User:
    user = await get_user_by_user_id(user_id, db_session)

    if user is None:
        raise ValueError("User does not exist")
    return user


async def update_user_service(
        user_id: UUID,
        parameters_to_change: dict,
        db_session: AsyncSession) -> User:
    user = await get_user_by_user_id(user_id, db_session)
    if user is None:
        raise ValueError("User does not exist")

    updated_user = await update_user(user, parameters_to_change, db_session)
    return updated_user


async def delete_user_service(user_id: UUID, db_session: AsyncSession):
    user = await get_user_by_user_id(user_id, db_session)
    if user is None:
        raise ValueError("User does not exist")

    deleted_user_id = await delete_user(user, db_session)
    return deleted_user_id


async def login_service(email: str, password: str, db_session: AsyncSession) -> dict:
    user = await get_user_by_email(email, db_session)
    if user is None:
        raise ValueError("User does not exist")

    if not check_password(user.hashed_password, password):
        raise AssertionError("Passwords do not match")

    access_token = create_jwt_token(
        email, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_jwt_token(
        email, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_token_service(token: str) -> dict:
    email: Optional[str] = get_email_from_token(token)
    if email is None:
        raise ValueError("Could not validate credentials")

    new_access_token: str = create_jwt_token(email, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }

