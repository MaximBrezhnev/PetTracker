from datetime import timedelta
from typing import Optional

from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from src.services import BaseService
from src.user.models import User
from src.user.services import security
from src.user.services.dal import UserDAL
from src.user.services.email import EmailService
from src.user.services.hashing import Hasher


class UserService(BaseService):
    def __init__(self, db_session: AsyncSession, dal_class):
        super().__init__(db_session, dal_class=dal_class)
        self.hasher = Hasher()
        self.email = EmailService()

    async def create_user_service(
            self,
            username: str,
            email: str,
            password: str
    ) -> None:
        """Service for create_user controller"""

        user: Optional[User] = await self.dal.get_user_by_email(
            email=email
        )

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
            email=[user.email, ],
            instance=user,
            subject="Письмо для подтверждения регистрации в PetTracker",
            template_name="email_confirmation.html"
        )

    async def verify_email_service(
            self,
            token: str,
    ) -> None:
        """Service for verify_email controller"""

        payload: dict = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user: Optional[User] = await self.dal.get_user_by_email(
            email=payload.get("email", None)
        )

        if user is None:
            raise JWTError("Could not validate credentials")

        await self.dal.activate_user(
            user=user
        )

    async def delete_user_service(
            self,
            user: User
    ) -> None:
        """Service for delete_user controller"""

        await self.dal.deactivate_user(user=user)

    async def login_service(
            self,
            username: str,
            password: str
    ) -> dict:
        """Service for login controller"""

        user: Optional[User] = await self.dal.get_user_by_username(
            username=username
        )

        if user is None:
            raise ValueError("User does not exist")

        if not user.is_active:
            raise ValueError("User does not exist")

        if not self.hasher.verify_password(user.hashed_password, password):
            raise ValueError("Passwords do not match")

        access_token: str = security.create_jwt_token(
            user.email, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token: str = security.create_jwt_token(
            user.email, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def refresh_token_service(user: User) -> dict:
        """Service for refresh_token controller"""

        new_access_token: str = security.create_jwt_token(
            email=user.email,
            exp_timedelta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    async def change_username_service(
            self,
            user: User,
            new_username: str
    ) -> User:
        """Service for change_username controller"""

        if user.username != new_username:
            updated_user: User = await self.dal.change_username(
                    user=user,
                    new_username=new_username
                )
            return updated_user

        return user

    async def change_password_service(
            self,
            user: User,
            old_password: str,
            new_password: str,
    ) -> User:
        """Service for change_password controller"""

        if not self.hasher.verify_password(
                user.hashed_password,
                old_password
        ):
            raise ValueError("Incorrect old password")

        updated_user: Optional[User] = await self.dal.change_password(
            user=user,
            new_password=self.hasher.get_password_hash(new_password),
        )

        return updated_user

    async def change_email_service(
            self,
            user: User,
            new_email: str
    ) -> None:
        """Service for change_email controller"""

        if user.email == new_email:
            raise ValueError("The user already uses this email")

        await self.email.send_email(
            email=[new_email, ],
            instance=user,
            subject="Письмо для подтверждения смены электронной почты в PetTracker",
            template_name="email_change_confirmation.html"
        )

    async def confirm_email_change_service(
            self,
            token: str
    ) -> User:
        """Service for confirm_email_change controller"""

        payload: dict = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
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

    async def reset_password_service(self, email: str) -> None:
        """Service for reset_password controller"""

        await self.email.send_email(
            email=[email, ],
            subject="Письмо для сброса пароля в PetTracker",
            template_name="password_reset_confirmation.html"
        )

    async def change_password_on_reset_service(
            self,
            token: str,
            new_password: str,
    ) -> User:
        """Service for change_password_on_reset controller"""

        payload: dict = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

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
