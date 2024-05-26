from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session
from src.user.models import User
from src.user.schemas import CreateUserDTO, ShowUserDTO, UpdateUserDTO

user_router = APIRouter(prefix="/user")


@user_router.post(path="/", response_model=ShowUserDTO)
async def create_user(
        body: CreateUserDTO,
        db_session: AsyncSession = Depends(get_db_session)
) -> ShowUserDTO:
    async with db_session.begin():
        query = select(User).where(User.email == body.email)
        resp = await db_session.execute(query)
        res = resp.fetchone()

        if res is not None:
            user = res[0]
            if user.is_active is False:
                return ShowUserDTO(
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email
                )
            raise HTTPException(
                status_code=409,
                detail="User with this credentials already exists"
            )

    try:
        async with db_session.begin():
            new_user = User(
                username=body.username,
                email=body.email,
                hashed_password=body.password1,
            )
            db_session.add(new_user)
            await db_session.flush()

        return ShowUserDTO(
            user_id=new_user.user_id,
            username=new_user.username,
            email=new_user.email,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="User with this credentials already exists"
        )


@user_router.get(path="/{user_id}", response_model=ShowUserDTO)
async def get_user(
    user_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
) -> ShowUserDTO:
    async with db_session.begin():
        query = select(User).where(User.user_id == user_id)
        resp = await db_session.execute(query)
        result = resp.fetchone()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    user = result[0]
    return ShowUserDTO(
        user_id=user.user_id,
        username=user.username,
        email=user.email
    )


@user_router.patch(path="/{user_id}", response_model=ShowUserDTO)
async def update_user(
        body: UpdateUserDTO,
        user_id: UUID,
        db_session: AsyncSession = Depends(get_db_session)
) -> ShowUserDTO:
    parameters_to_change = body.dict(exclude_none=True)

    if not parameters_to_change:
        raise HTTPException(
            status_code=400,
            detail="At least one parameter must be provided"
        )

    async with db_session.begin():
        query = select(User).where(User.user_id == user_id)
        resp = await db_session.execute(query)
        result = resp.fetchone()
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    user = result[0]

    try:
        async with db_session.begin():
            query = (
                update(User)
                .where(User.user_id == user.user_id)
                .values(**parameters_to_change)
                .returning(User)
            )
            result = await db_session.execute(query)
            updated_user = result.fetchone()[0]
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="User with this credentials already exists"
        )

    return ShowUserDTO(
        user_id=updated_user.user_id,
        username=updated_user.username,
        email=updated_user.email
    )


@user_router.delete(path="/{user_id}")
async def delete_user(
    user_id: UUID,
    db_session: AsyncSession = Depends(get_db_session)
):
    async with db_session.begin():
        query = select(User).where(User.user_id == user_id)
        resp = await db_session.execute(query)
        result = resp.fetchone()
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    user = result[0]

    async with db_session.begin():
        query = (
            update(User)
            .where(User.user_id == user.user_id)
            .values(is_active=False)
        )
        await db_session.execute(query)

    return {"message": f"User with id {user_id} deleted successfully"}
