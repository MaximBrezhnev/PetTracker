from datetime import timedelta
from typing import Optional

from jose import jwt
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import project_settings
from src.services import BaseService
from src.user.models import User
from src.user.services import security
from src.user.services.email import EmailService
from src.user.services.hashing import Hasher


class UserService(BaseService):
    """Service representing business logic
    used by the endpoints of user_router"""

    def __init__(self, db_session: AsyncSession, dal_class: type):
        """Initializes UserService by binding sub services"""

        super().__init__(db_session=db_session, dal_class=dal_class)
        self.hasher: Hasher = Hasher()
        self.email: EmailService = EmailService()

    async def create_user(self, username: str, email: str, password: str) -> None:
        """Creates new user or update the current one
        if the user already exists and is inactive. If the user exists
        but is active then raises an exception"""

        user: Optional[User] = await self.dal.get_user_by_email(email=email)

        if user is not None:
            if user.is_active:
                raise ValueError("User already exists")

            await self.dal.update_username_and_password(
                username=username,
                password=self.hasher.get_password_hash(password),
                user=user,
            )

        else:
            user: User = await self.dal.create_new_user(
                username=username,
                email=email,
                hashed_password=self.hasher.get_password_hash(password),
            )

        await self.email.send_email(
            email=[
                user.email,
            ],
            instance=user,
            subject="Письмо для подтверждения регистрации в PetTracker",
            template_name="email_confirmation.html",
        )

    async def verify_email(
        self,
        token: str,
    ) -> None:
        """Verifies email using the provided token"""

        payload: dict = jwt.decode(
            token, project_settings.SECRET_KEY, algorithms=["HS256"]
        )
        user: Optional[User] = await self.dal.get_user_by_email(
            email=payload.get("email", None)
        )

        if user is None:
            raise JWTError("Could not validate credentials")

        await self.dal.activate_user(user=user)

    async def delete_user(self, user: User) -> None:
        """Deletes user from database"""

        await self.dal.deactivate_user(user=user)

    async def login(self, username: str, password: str) -> dict:
        """Logs the user into the system"""

        user: Optional[User] = await self.dal.get_user_by_username(username=username)

        if user is None:
            raise ValueError("User does not exist")

        if not user.is_active:
            raise ValueError("User does not exist")

        if not self.hasher.verify_password(user.hashed_password, password):
            raise ValueError("Passwords do not match")

        access_token: str = security.create_jwt_token(
            user.email, timedelta(minutes=project_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token: str = security.create_jwt_token(
            user.email, timedelta(days=project_settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def refresh_token(user: User) -> dict:
        """Returns new access token based on the received one"""

        new_access_token: str = security.create_jwt_token(
            email=user.email,
            exp_timedelta=timedelta(
                minutes=project_settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        )
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    async def change_username(self, user: User, new_username: str) -> User:
        """Changes username if new one does not match the current one"""

        if user.username != new_username:
            updated_user: User = await self.dal.change_username(
                user=user, new_username=new_username
            )
            return updated_user

        return user

    async def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str,
    ) -> User:
        """Changes user's password if the provided old password is correct"""

        if not self.hasher.verify_password(user.hashed_password, old_password):
            raise ValueError("Incorrect old password")

        updated_user: Optional[User] = await self.dal.change_password(
            user=user,
            new_password=self.hasher.get_password_hash(new_password),
        )

        return updated_user

    async def change_email(self, user: User, new_email: str) -> None:
        """Sends email for email change confirmation if the provided
        email does not match the current one"""

        if user.email == new_email:
            raise ValueError("The user already uses this email")

        await self.email.send_email(
            email=[
                new_email,
            ],
            instance=user,
            subject="Письмо для подтверждения смены электронной почты в PetTracker",
            template_name="email_change_confirmation.html",
        )

    async def confirm_email_change(self, token: str) -> User:
        """Changes user's email if the provided token is correct"""

        payload: dict = jwt.decode(
            token, project_settings.SECRET_KEY, algorithms=["HS256"]
        )
        user: Optional[User] = await self.dal.get_user_by_user_id(
            user_id=payload.get("current_user_id", None)
        )

        if user is None:
            raise JWTError("Could not validate credentials")

        if not user.is_active:
            raise ValueError("User does not exist")

        new_email: str = payload.get("email", None)
        if new_email is None:
            raise JWTError("Could not validate credentials")

        updated_user: User = await self.dal.change_email(
            user=user,
            new_email=new_email,
        )

        return updated_user

    async def reset_password(self, email: str) -> None:
        """Sends email for password reset"""

        await self.email.send_email(
            email=[
                email,
            ],
            subject="Письмо для сброса пароля в PetTracker",
            template_name="password_reset_confirmation.html",
        )

    async def change_password_on_reset(
        self,
        token: str,
        new_password: str,
    ) -> User:
        """Changes user's password if the provided token is correct"""

        payload: dict = jwt.decode(
            token, project_settings.SECRET_KEY, algorithms=["HS256"]
        )

        user: Optional[User] = await self.dal.get_user_by_email(
            email=payload.get("email", None),
        )

        if user is None:
            raise ValueError("User does not exist")

        if not user.is_active:
            raise ValueError("User does not exist")

        updated_user: User = await self.dal.change_password(
            user=user,
            new_password=self.hasher.get_password_hash(new_password),
        )

        return updated_user
