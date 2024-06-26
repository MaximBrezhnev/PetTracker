from typing import Optional
from uuid import UUID

from sqlalchemy import Result
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload

from src.services import BaseDAL
from src.user.models import User


class UserDAL(BaseDAL):
    """Data access layer service that enables to work with user data"""

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Gets user from database by its email"""

        async with self.db_session.begin():
            query: Select = (
                select(User).filter_by(email=email).options(selectinload(User.pets))
            )
            result: Result = await self.db_session.execute(query)
            return result.scalars().first()

    async def update_username_and_password(
        self,
        username: str,
        password: str,
        user: User,
    ) -> None:
        """Updates username and password if they do not match existing ones"""

        async with self.db_session.begin():
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
        """Creates new user in database"""

        async with self.db_session.begin():
            new_user: User = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
            )
            self.db_session.add(new_user)
            await self.db_session.flush()

            return new_user

    async def activate_user(self, user: User) -> None:
        """Sets is_active parameter to True"""

        if not user.is_active:
            async with self.db_session.begin():
                setattr(user, "is_active", True)

    async def get_user_by_user_id(self, user_id: UUID) -> User:
        """Gets user from database by its id"""

        async with self.db_session.begin():
            result: Result = await self.db_session.execute(
                select(User).filter_by(user_id=user_id)
            )
            return result.scalars().first()

    async def deactivate_user(self, user: User) -> None:
        """Sets is_active parameter to False"""

        async with self.db_session.begin():
            await self.db_session.execute(
                update(User).filter_by(user_id=user.user_id).values(is_active=False)
            )

    async def change_username(self, user: User, new_username: str) -> User:
        """Changes username of the provided user"""

        async with self.db_session.begin():
            result: Result = await self.db_session.execute(
                update(User)
                .filter_by(user_id=user.user_id)
                .values(username=new_username)
                .returning(User)
            )
            return result.scalars().first()

    async def change_password(self, user: User, new_password: str) -> User:
        """Changes password of the provided user"""

        async with self.db_session.begin():
            result: Result = await self.db_session.execute(
                update(User)
                .filter_by(user_id=user.user_id)
                .values(hashed_password=new_password)
                .returning(User)
            )
            return result.scalars().first()

    async def change_email(self, user: User, new_email: str) -> User:
        """Changes email of the provided user"""

        async with self.db_session.begin():
            setattr(user, "email", new_email)
            return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Gets user from database by its username"""

        async with self.db_session.begin():
            result: Result = await self.db_session.execute(
                select(User).filter_by(username=username)
            )
            return result.scalars().first()
