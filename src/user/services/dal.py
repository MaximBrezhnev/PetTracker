from typing import Optional
from uuid import UUID

from sqlalchemy import select, Select, Result
from sqlalchemy.orm import selectinload

from src.services import BaseDAL
from src.user.models import User


class UserDAL(BaseDAL):
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """DAL service that gets user by its email"""

        query: Select = (
            select(User).
            filter_by(email=email).
            options(selectinload(User.pets))
        )
        result: Result = await self.db_session.execute(query)

        return result.scalars().first()

    async def update_username_and_password(
            self,
            username: str,
            password: str,
            user: User,
    ) -> None:
        """DAL service that updates username and password if they do not match existing ones"""

        async with self.db_session:
            if username != user.username:
                setattr(user, "username", username)

            if password != user.hashed_password:
                setattr(user, "hashed_password", password)

    async def create_new_user(
            self,
            username: str,
            email: str,
            hashed_password: str,
    ) -> User:
        """DAL service that creates new user in database"""

        new_user: User = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
        )
        self.db_session.add(new_user)
        await self.db_session.flush()

        return new_user

    async def activate_user(self, user: User) -> None:
        """DAL service that activates user after successful email verification"""

        if not user.is_active:
            async with self.db_session:
                setattr(user, "is_active", True)

    async def get_user_by_user_id(self, user_id: UUID) -> User:
        """DAL service that gets user by its id"""

        result: Result = await self.db_session.execute(
            select(User).filter_by(user_id=user_id)
        )
        return result.scalars().first()

    async def deactivate_user(self, user: User) -> None:
        """DAL service that deactivates user"""

        async with self.db_session:
            setattr(user, "is_active", False)

    async def change_username(self, user: User, new_username: str) -> User:
        """DAL service that change username"""

        async with self.db_session:
            setattr(user, "username", new_username)

        return user

    async def change_password(self, user: User, new_password: str) -> User:
        """DAL service that changes password"""

        async with self.db_session:
            setattr(user, "hashed_password", new_password)

        return user

    async def change_email(self, user: User, new_email: str) -> User:
        """DAL service that changes email after email change confirmation"""

        async with self.db_session:
            setattr(user, "email", new_email)

        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """DAL service that gets user by its email"""

        result: Result = await self.db_session.execute(
            select(User).filter_by(username=username)
        )
        return result.scalars().first()
