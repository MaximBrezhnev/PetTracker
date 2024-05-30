from datetime import timedelta
from typing import Optional
from uuid import UUID

from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from src.user.models import User
from src.user.schemas import CreateUserDTO, ChangePasswordDTO
from src.user.services.auth_services import check_password, create_jwt_token, get_email_from_token, get_password_hash
from src.user.services.dal_services import get_user_by_email, update_username_and_password, create_new_user, \
    update_user_upon_verification, get_user_by_user_id, delete_user, change_username, \
    change_password, update_user_when_changing_email, change_password_on_reset
from src.user.services.email_servcies import send_email


async def create_user_service(body: CreateUserDTO, db_session: AsyncSession) -> None:
    user = await get_user_by_email(body.email, db_session)

    if user is not None:
        if user.is_active:
            raise ValueError("User already exists")
        await update_username_and_password(body.username, body.password1, user, db_session)

    else:
        user = await create_new_user(body.username, body.email, body.password1, db_session)

    await send_email(
        email=[user.email, ],
        instance=user,
        subject="Письмо для подтверждения регистрации в PetTracker",
        template_name="confirmation_email.html"
    )


async def verify_email_service(token: str, db_session: AsyncSession) -> None:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = await get_user_by_email(payload.get("email", None), db_session)

    if user is None:
        raise ValueError("User does not exist")

    await update_user_upon_verification(user, db_session)


async def get_user_service(user_id: UUID, db_session: AsyncSession) -> User:
    user = await get_user_by_user_id(user_id, db_session)

    if user is None:
        raise ValueError("User does not exist")
    return user


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


async def change_username_service(user: User, new_username: str, db_session: AsyncSession) -> User:
    if user.username != new_username:
        updated_user: User = await change_username(user, new_username, db_session)
        return updated_user
    return user


async def change_password_service(user: User, body: ChangePasswordDTO, db_session: AsyncSession) -> User:
    if user.hashed_password != body.old_password:
        raise ValueError("Incorrect old password")

    updated_user: User = await change_password(user, body.new_password1, db_session)
    return updated_user


async def change_email_service(user: User, new_email: str) -> None:
    if user.email == new_email:
        raise ValueError("The user already uses this email")
    await send_email(
        email=[new_email, ],
        instance=user,
        subject="Письмо для подтверждения смены электронной почты в PetTracker",
        template_name="confirmation_of_email_change.html"
    )


async def confirm_email_change_service(token: str, db_session: AsyncSession) -> None:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user = await get_user_by_user_id(payload.get("current_user_id", None), db_session)

    if user is None:
        raise ValueError("User does not exist")

    await update_user_when_changing_email(user, payload.get("email", None), db_session)


async def reset_password_service(email: str) -> None:
    print(get_password_hash("eddd"))
    await send_email(
        email=[email, ],
        subject="Письмо для сброса пароля в PetTracker",
        template_name="password_reset.html"
    )


async def change_password_on_reset_service(
        token: str,
        new_password: str,
        db_session: AsyncSession
) -> User:
    payload: dict = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user: User = await get_user_by_email(
        email=payload.get("email", None),
        db_session=db_session
    )

    if user is None:
        raise ValueError("User does not exist")

    updated_user: User = await change_password_on_reset(
        user=user,
        new_password=new_password,
        db_session=db_session
    )
    return updated_user
