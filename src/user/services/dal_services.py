from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.user.models import User


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


async def change_username(user: User, new_username: str, db_session: AsyncSession) -> User:
    async with db_session.begin():
        query = (
            update(User).where(User.email == user.email).
            values(username=new_username).returning(User)
        )
        result = await db_session.execute(query)

    return result.fetchone()[0]


async def change_password(user: User, new_password: str, db_session: AsyncSession) -> User:
    async with db_session.begin():
        query = (
            update(User).where(User.email == user.email).
            values(hashed_password=new_password).returning(User)
        )
        result = await db_session.execute(query)

    return result.fetchone()[0]


async def update_user_when_changing_email(user: User, new_email: str, db_session: AsyncSession) -> None:
    if user.is_active:
        async with db_session.begin():
            query = update(User).where(User.user_id == user.user_id).values(email=new_email)
            await db_session.execute(query)


async def change_password_on_reset(user: User, new_password: str, db_session: AsyncSession) -> User:
    if user.is_active:
        async with db_session.begin():
            query = (
                update(User).where(User.user_id == user.user_id).
                values(hashed_password=new_password).returning(User)
            )
            result = await db_session.execute(query)

        return result.fetchone()[0]
