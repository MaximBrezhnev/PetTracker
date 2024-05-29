from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.models import User


# 1. Подумать над реализацией с помощью класса
# 2. Подумать над тем, чтобы усовершенствовать get

async def get_user_by_email(
        email: str, db_session: AsyncSession) -> Optional[User]:
    async with db_session.begin():
        query = select(User).where(User.email == email)
        result = await db_session.execute(query)
        data_from_result = result.fetchone()

        if data_from_result is not None:
            return data_from_result[0]


async def update_username_and_password(
        username: str,
        password: str,
        user: User,
        db_session: AsyncSession) -> None:
    async with db_session.begin():
        if username != user.username:
            query = update(User).where(User.username == user.username).values(
                username=username,
            )
            await db_session.execute(query)

        if password != user.hashed_password:
            query = update(User).where(User.username == user.username).values(
                hashed_password=password,
            )
            await db_session.execute(query)


async def create_new_user(
        username: str,
        email: str,
        password: str,
        db_session: AsyncSession) -> User:
    async with db_session.begin():
        new_user = User(
            username=username,
            email=email,
            hashed_password=password,
        )
        db_session.add(new_user)
        await db_session.flush()

    return new_user


async def get_user_by_username(
        username: str, db_session: AsyncSession) -> Optional[User]:
    async with db_session.begin():
        query = select(User).where(User.username == username)
        result = await db_session.execute(query)
        data_from_result = result.fetchone()

        if data_from_result is not None:
            return data_from_result[0]


async def update_user_upon_verification(
        user: User, db_session: AsyncSession) -> None:
    if user.is_active is False:
        async with db_session.begin():
            query = update(User).where(User.email == user.email). \
                values(is_active=True)
            await db_session.execute(query)


async def get_user_by_user_id(
        user_id: UUID, db_session: AsyncSession) -> User:
    async with db_session.begin():
        query = select(User).where(User.user_id == user_id)
        result = await db_session.execute(query)
        data_from_result = result.fetchone()

        if data_from_result is not None:
            return data_from_result[0]


async def update_user(
        user: User,
        parameters_to_change: dict,
        db_session: AsyncSession) -> User:
    async with db_session.begin():
        query = (
            update(User)
            .where(User.user_id == user.user_id)
            .values(**parameters_to_change)
            .returning(User)
        )
        result = await db_session.execute(query)
        return result.fetchone()[0]


async def delete_user(user: User, db_session: AsyncSession) -> UUID:
    with db_session.begin():
        query = (
            update(User)
            .where(User.user_id == user.user_id)
            .values(is_active=False)
        )
        result = await db_session.execute(query)

    deleted_user = result.fetchone()[0]
    return deleted_user.user_id

