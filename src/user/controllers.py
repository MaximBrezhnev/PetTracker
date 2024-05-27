import os
from datetime import timedelta, datetime
from uuid import UUID

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose import JWTError
from fastapi import Depends, HTTPException, Request
from fastapi.routing import APIRouter
from sqlalchemy import select, update, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import status

from src.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS
from src.dependencies import get_db_session
from src.user.email import SECRET_KEY
from src.user.models import User
from src.user.schemas import CreateUserDTO, ShowUserDTO, UpdateUserDTO, TokenDTO, LoginDTO
from src.user.email import send_email

user_router = APIRouter(prefix="/user")

templates_directory = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_directory)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


@user_router.post(path="/", response_model=ShowUserDTO)
async def create_user(
        body: CreateUserDTO,
        db_session: AsyncSession = Depends(get_db_session)
) -> ShowUserDTO:
    # Блок проверки, что пользователь уже имел аккаунт
    async with db_session.begin():
        query = select(User).where(User.email == body.email)
        resp = await db_session.execute(query)
        res = resp.fetchone()

        if res is not None:
            user = res[0]

            if body.username != user.username:
                query = update(User).where(User.username == user.username).values(
                    username=body.username,
                    hashed_password=body.password1
                )
                await db_session.execute(query)

            if user.is_active is False:
                await send_email(email=[user.email, ], instance=user)
                return ShowUserDTO(
                    user_id=user.user_id,
                    username=user.username,
                    email=user.email
                )

            raise HTTPException(
                status_code=409,
                detail="User with this credentials already exists"
            )
    #######################################################################

    try:
        async with db_session.begin():
            new_user = User(
                username=body.username,
                email=body.email,
                hashed_password=body.password1,
            )
            db_session.add(new_user)
            await db_session.flush()

        print(new_user.user_id)
        await send_email(email=[new_user.email, ], instance=new_user)
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


@user_router.get(path="/verification")
async def verify_email(
    request: Request,
    token: str,
    db_session: AsyncSession = Depends(get_db_session)
) -> HTMLResponse:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        try:
            async with (db_session.begin()):
                query = (
                    select(User).
                    where(and_(User.user_id == payload.get("user_id"),
                          User.username == payload.get("username")))
                )
                resp = await db_session.execute(query)
                user = resp.fetchone()[0]
                if not user.is_active:
                    user.is_active = True
                    query = update(User).values(is_active=True)
                    await db_session.execute(query)
                    return templates.TemplateResponse(
                        "successful_verification.html",
                        {"request": request}
                    )

        except:
            return templates.TemplateResponse(
                "failed_verification.html",
                {"request": request}
            )
    except:
        return templates.TemplateResponse(
            "failed_verification.html",
            {"request": request}
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


@user_router.post(path="/login", response_model=TokenDTO)
async def login(
    body: LoginDTO,
    db_session: AsyncSession = Depends(get_db_session)
) -> TokenDTO:
    # обработка исключений и получение user
    async with db_session.begin():
        query = select(User).where(User.email == body.email)
        resp = await db_session.execute(query)
        res = resp.fetchone()

        if res is None:
            raise HTTPException(
                status_code=404,
                detail={"message": "User with this email does not exist"}
            )

        user = res[0]
        if user.hashed_password != body.password:
            raise HTTPException(
                status_code=401,
                detail={"message": "Provided password is incorrect"}
            )
    #######################################

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data = {"sub": user.email}
    to_encode = data.copy()
    expire = datetime.utcnow() + access_token_expires
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM
    )

    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data = {"sub": user.email}
    to_encode = data.copy()
    expire = datetime.utcnow() + refresh_token_expires
    to_encode.update({"exp": expire})
    encoded_refresh_jwt = jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM
    )

    return TokenDTO(
        access_token=encoded_jwt,
        refresh_token=encoded_refresh_jwt,
        token_type="bearer"
    )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return email


@user_router.post(path="/token/refresh")
async def refresh_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        data = {"sub": email}
        to_encode = data.copy()
        expire = datetime.utcnow() + access_token_expires
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, SECRET_KEY, algorithm=ALGORITHM
        )
        return TokenDTO(
            access_token=encoded_jwt,
            token_type="bearer"
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


# Тестовая ручка для проверки работы access токена
# @user_router.get("/test/me")
# async def read_users_me(current_user: User = Depends(get_current_user)):
#     return {"message": current_user}
