from typing import Optional
from uuid import UUID

from sqlalchemy import select, update, Select, Result, Row, Update
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.models import User


async def get_user_by_email(
        email: str, db_session: AsyncSession) -> Optional[User]:
    """DAL service that gets user by its email"""

    async with db_session.begin():
        query: Select = select(User).where(User.email == email)
        result: Result = await db_session.execute(query)
        data_from_result: Optional[Row] = result.fetchone()

        if data_from_result is not None:
            return data_from_result[0]


async def update_username_and_password(
        username: str,
        password: str,
        user: User,
        db_session: AsyncSession) -> None:
    """DAL service that updates username and password if they do not match existing ones"""

    async with db_session.begin():
        if username != user.username:
            query: Update = update(User).where(User.username == user.username).values(
                username=username,
            )
            await db_session.execute(query)

        if password != user.hashed_password:
            query: Update = update(User).where(User.username == user.username).values(
                hashed_password=password,
            )
            await db_session.execute(query)


async def create_new_user(
        username: str,
        email: str,
        hashed_password: str,
        db_session: AsyncSession) -> User:
    """DAL service that creates new user in database"""

    async with db_session.begin():
        new_user: User = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
        )
        db_session.add(new_user)
        await db_session.flush()

    return new_user


async def update_user_upon_verification(
        user: User, db_session: AsyncSession) -> None:
    """DAL service that activates user after successful email verification"""

    if not user.is_active:
        async with (db_session.begin()):
            query: Update = (
                update(User).
                where(User.email == user.email).
                values(is_active=True)
            )
            await db_session.execute(query)


async def get_user_by_user_id(
        user_id: UUID, db_session: AsyncSession) -> User:
    """DAL service that gets user by its id"""

    async with db_session.begin():
        query: Select = select(User).where(User.user_id == user_id)
        result: Result = await db_session.execute(query)
        data_from_result: Optional[Row] = result.fetchone()

        if data_from_result is not None:
            return data_from_result[0]


async def delete_user(user: User, db_session: AsyncSession) -> None:
    """DAL service that deactivates user"""

    async with db_session.begin():
        query: Update = (
            update(User)
            .where(User.user_id == user.user_id)
            .values(is_active=False)
        )
        await db_session.execute(query)


async def change_username(user: User, new_username: str, db_session: AsyncSession) -> User:
    """DAL service that change username"""

    async with db_session.begin():
        query: Update = (
            update(User).where(User.email == user.email).
            values(username=new_username).returning(User)
        )
        result: Result = await db_session.execute(query)

    return result.fetchone()[0]


async def change_password(user: User, new_password: str, db_session: AsyncSession) -> User:
    """DAL service that changes password"""

    async with db_session.begin():
        query: Update = (
            update(User).where(User.email == user.email).
            values(hashed_password=new_password).returning(User)
        )
        result: Result = await db_session.execute(query)

    return result.fetchone()[0]


async def update_user_when_changing_email(user: User, new_email: str, db_session: AsyncSession) -> User:
    """DAL service that changes email after email change confirmation"""

    async with db_session.begin():
        query: User = (
            update(User).where(User.user_id == user.user_id).
            values(email=new_email).returning(User)
        )
        result: Result = await db_session.execute(query)
    return result.fetchone()[0]


async def get_user_by_username(
        username: str, db_session: AsyncSession) -> Optional[User]:
    """DAL service that gets user by its email"""

    async with db_session.begin():
        query: Select = select(User).where(User.username == username)
        result: Result = await db_session.execute(query)
        data_from_result: Optional[Row] = result.fetchone()

        if data_from_result is not None:
            return data_from_result[0]
