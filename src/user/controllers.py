from aiosmtplib import SMTPRecipientsRefused, SMTPDataError
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from starlette.responses import JSONResponse

from src.dependencies import get_db_session, oauth2_scheme, get_current_user
from src.user.exceptions import email_sending_exception, credentials_exception
from src.user.models import User
from src.user.schemas import CreateUserDTO, ShowUserDTO, TokenDTO, ChangeUsernameDTO, ChangePasswordDTO, \
    EmailDTO, ResetPasswordDTO
from src.user.services.services import create_user_service, verify_email_service, \
    delete_user_service, login_service, refresh_token_service, change_username_service, change_password_service, \
    change_email_service, confirm_email_change_service, reset_password_service, change_password_on_reset_service


user_router = APIRouter(prefix="/user")


@user_router.post(path="/")
async def create_user(
        body: CreateUserDTO,
        db_session: AsyncSession = Depends(get_db_session)) -> JSONResponse:
    """
    Controller that creates inactive user. If inactive user with this email exists,
    it updates username and password. Then it sends an activation email
    """

    try:
        await create_user_service(body, db_session)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "confirmation email was sent"}
        )

    except (ValueError, IntegrityError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this credentials already exists"
        )

    except (SMTPRecipientsRefused, SMTPDataError):
        raise email_sending_exception


@user_router.get(path="/verification")
async def verify_email(
        token: str,
        db_session: AsyncSession = Depends(get_db_session)) -> JSONResponse:
    """Controller that verifies email after registration"""

    try:
        await verify_email_service(token, db_session)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "The email was verified successfully"}
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Cannot verify email"}
        )


@user_router.get(path="/", response_model=ShowUserDTO)
async def get_user(user: User = Depends(get_current_user)) -> ShowUserDTO:
    """Controller that returns user data for profile"""

    return user


@user_router.delete(path="/")
async def delete_user(
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)) -> JSONResponse:
    """Controller that deactivates user"""

    await delete_user_service(user, db_session)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"The user deleted successfully"}
    )


@user_router.post(path="/auth/login", response_model=TokenDTO)
async def login(
        body: OAuth2PasswordRequestForm = Depends(),
        db_session: AsyncSession = Depends(get_db_session)) -> TokenDTO:
    """Controller for user authentication and authorization"""

    try:
        token_data: dict = await login_service(body.username, body.password, db_session)
        return TokenDTO(**token_data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Incorrect username or password"}
        )


@user_router.post(path="/auth/refresh-token", response_model=TokenDTO)
async def refresh_token(
        user: User = Depends(get_current_user),
) -> TokenDTO:
    """Controller that refreshes access token"""

    token_data: dict = refresh_token_service(user)
    return TokenDTO(**token_data)


@user_router.patch(path='/change-username', response_model=ShowUserDTO)
async def change_username(
        body: ChangeUsernameDTO,
        user: User = Depends(get_current_user),
        db_session: AsyncSession = Depends(get_db_session)) -> ShowUserDTO:
    """Controller for username changing"""

    try:
        updated_user: User = await change_username_service(user, body.username, db_session)
        return updated_user

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
    """Controller for password changing"""

    try:
        updated_user: User = await change_password_service(user, body, db_session)
        return updated_user

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password was provided"
        )


@user_router.patch(path="/change-email")
async def change_email(
        body: EmailDTO,
        user: User = Depends(get_current_user)) -> JSONResponse:
    """Controller that sends email to confirm the email change"""

    try:
        await change_email_service(new_email=body.email, user=user)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Email for email change confirmation was sent"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "The user already uses this email"}
        )
    except (SMTPRecipientsRefused, SMTPDataError):
        raise email_sending_exception

    
@user_router.get(path="/change-email/confirmation", response_model=ShowUserDTO)
async def confirm_email_change(
        token: str,
        db_session: AsyncSession = Depends(get_db_session)) -> ShowUserDTO:
    """Controller that changes email"""

    try:
        updated_user: User = await confirm_email_change_service(token, db_session)
        return updated_user

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "User with this email already exists"}
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Could not validate credentials"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User does not exist"}
        )


@user_router.post(path="/auth/reset-password")
async def reset_password(body: EmailDTO) -> JSONResponse:
    """Controller that sends email to confirm password reset"""

    try:
        await reset_password_service(body.email)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Password reset email was sent"}
        )
    except (SMTPRecipientsRefused, SMTPDataError):
        raise email_sending_exception


@user_router.patch(path="/auth/reset-password/confirmation", response_model=ShowUserDTO)
async def change_password_on_reset(
        body: ResetPasswordDTO,
        db_session: AsyncSession = Depends(get_db_session)) -> ShowUserDTO:
    """Controller that changes password on reset"""

    try:
        updated_user: User = await change_password_on_reset_service(body.token, body.password1, db_session)
        return updated_user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Could not validate credentials"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "User does not exist"}
        )
