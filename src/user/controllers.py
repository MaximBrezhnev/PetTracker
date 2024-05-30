import os
from uuid import UUID

from aiosmtplib import SMTPRecipientsRefused, SMTPDataError
from jose import JWTError
from fastapi import Depends, HTTPException, Request
from fastapi.routing import APIRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
from starlette.responses import JSONResponse

from src.dependencies import get_db_session
from src.user.dependencies import oauth2_scheme, get_current_user
from src.user.models import User
from src.user.schemas import CreateUserDTO, ShowUserDTO, TokenDTO, LoginDTO, ChangeUsernameDTO, ChangePasswordDTO, \
    EmailDTO, ResetPasswordDTO
from src.user.services.services import create_user_service, verify_email_service, get_user_service, \
    delete_user_service, login_service, refresh_token_service, change_username_service, change_password_service, \
    change_email_service, confirm_email_change_service, reset_password_service, change_password_on_reset_service

user_router = APIRouter(prefix="/user")

templates_directory = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_directory)


@user_router.post(path="/")
async def create_user(
        body: CreateUserDTO,
        db_session: AsyncSession = Depends(get_db_session)) -> JSONResponse:
    try:
        await create_user_service(body, db_session)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "confirmation email was sent"}
        )

    except (ValueError, IntegrityError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this credentials already exists"
        )

    except (SMTPRecipientsRefused, SMTPDataError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot send email"
        )


@user_router.get(path="/verification")
async def verify_email(
        request: Request,
        token: str,
        db_session: AsyncSession = Depends(get_db_session)) -> HTMLResponse:
    try:
        await verify_email_service(token, db_session)
        return templates.TemplateResponse(
            "confirmation_result.html",
            {
                "request": request,
                "header": "Вы успешно зарегистрировались в PetTracker",
                "message": "Теперь вы можете вернуться к ресурсу и войти с введенными вами данными"
            }
        )
    except (ValueError, JWTError):
        return templates.TemplateResponse(
            "confirmation_result.html",
            {
                "request": request,
                "header": "Что-то пошло не так",
                "message": "К сожалению, подтвердить вашу почту не удалось. Возможно, ссылка недействительна или "
                           "истекла. Пожалуйста, запросите новую ссылку для подтверждения."
            }
        )


@user_router.get(path="/{user_id}", response_model=ShowUserDTO)
async def get_user(
        user_id: UUID,
        db_session: AsyncSession = Depends(get_db_session)) -> ShowUserDTO:
    try:
        user = await get_user_service(user_id, db_session)
        return ShowUserDTO(
            user_id=user.user_id,
            username=user.username,
            email=user.email
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@user_router.delete(path="/{user_id}")
async def delete_user(
        user_id: UUID,
        db_session: AsyncSession = Depends(get_db_session)) -> JSONResponse:
    try:
        deleted_user_id = await delete_user_service(user_id, db_session)
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content={"message": f"User with id {deleted_user_id} deleted successfully"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@user_router.post(path="/auth/login", response_model=TokenDTO)
async def login(
        body: LoginDTO,
        db_session: AsyncSession = Depends(get_db_session)) -> TokenDTO:
    try:
        token_data = await login_service(body.email, body.password, db_session)
        return TokenDTO(**token_data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User with this email does not exist"}
        )
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Provided password is incorrect"}
        )


@user_router.post(path="/auth/refresh-token", response_model=TokenDTO)
async def refresh_token(token: str = Depends(oauth2_scheme)) -> TokenDTO:
    try:
        token_data = refresh_token_service(token)
        return TokenDTO(**token_data)
    except (ValueError, JWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@user_router.patch(path='/change-username', response_model=ShowUserDTO)
async def change_username(
        body: ChangeUsernameDTO,
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)) -> ShowUserDTO:
    try:
        updated_user: User = await change_username_service(user, body.username, db_session)
        return ShowUserDTO(
            user_id=updated_user.user_id,
            username=updated_user.username,
            email=updated_user.email,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this username already exists"
        )


@user_router.patch(path="/change-password", response_model=ShowUserDTO)
async def change_password(
        body: ChangePasswordDTO,
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)) -> ShowUserDTO:
    try:
        updated_user: User = await change_password_service(user, body, db_session)
        return ShowUserDTO(
            user_id=updated_user.user_id,
            username=updated_user.username,
            email=updated_user.email,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password was provided"
        )


@user_router.patch(path="/change-email")
async def change_email(
        body: EmailDTO,
        user: User = Depends(get_current_user)) -> JSONResponse:
    try:
        await change_email_service(new_email=body.email, user=user)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Email for confirmation of email change was sent"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "The user already uses this email"}
        )
    except (SMTPRecipientsRefused, SMTPDataError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot send email"
        )

    
@user_router.get(path="/change-email/confirmation")
async def confirm_email_change(
        request: Request,
        token: str,
        db_session: AsyncSession = Depends(get_db_session)) -> HTMLResponse:
    try:
        await confirm_email_change_service(token, db_session)
        return templates.TemplateResponse(
            "confirmation_result.html",
            {
                "request": request,
                "header": "Вы успешно сменили почту",
                "message": "Теперь вы можете вернуться в свой профиль в PetTracker"
            }
        )
    except IntegrityError:
        return templates.TemplateResponse(
            "confirmation_result.html",
            {
                "request": request,
                "header": "Не удалось сменить электронную почту",
                "message": "В PetTracker уже существует аккаунт, привязанный к этой почте"
            }
        )
    except (ValueError, JWTError):
        return templates.TemplateResponse(
            "confirmation_result.html",
            {
                "request": request,
                "header": "Что-то пошло не так",
                "message": "К сожалению, подтвердить смену почты не удалось. Возможно, ссылка недействительна или "
                           "истекла. Пожалуйста, запросите новую ссылку для подтверждения."
            }
        )


@user_router.post(path="/auth/reset-password")
async def reset_password(body: EmailDTO) -> JSONResponse:
    try:
        await reset_password_service(body.email)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Password reset email was sent"}
        )
    except (SMTPRecipientsRefused, SMTPDataError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot send email"
        )


@user_router.patch(path="auth/reset-password/confirmation", response_model=ShowUserDTO)
async def change_password_on_reset(
        token: str,
        body: ResetPasswordDTO,
        db_session: AsyncSession = Depends(get_db_session)) -> ShowUserDTO:
    try:
        updated_user = await change_password_on_reset_service(token, body.new_password1, db_session)
        return ShowUserDTO(
            user_id=updated_user.user_id,
            username=updated_user.username,
            email=updated_user.email
        )
    except (ValueError, JWTError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Could not validate credentials"}
        )
    except (SMTPRecipientsRefused, SMTPDataError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot send email"
        )
