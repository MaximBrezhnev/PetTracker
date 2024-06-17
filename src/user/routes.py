from aiosmtplib import SMTPRecipientsRefused, SMTPDataError
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy.exc import IntegrityError
from fastapi import status
from starlette.responses import JSONResponse

from src.dependencies import get_current_user
from src.exceptions import email_sending_exception
from src.user.dependencies import get_user_service
from src.user.models import User
from src.user.schemas import CreateUserSchema, ShowUserSchema, TokenSchema, ChangeUsernameSchema, \
    ChangePasswordSchema, EmailSchema, ResetPasswordSchema
from src.user.services.services2 import UserService


user_router = APIRouter(
    prefix="/user",
    tags=["user", ]
)


@user_router.post(path="/")
async def create_user(
        body: CreateUserSchema,
        user_service: UserService = Depends(get_user_service)
) -> JSONResponse:
    """
    Controller that creates inactive user. If inactive user with this email exists,
    it updates username and password. Then it sends an activation email
    """

    try:
        await user_service.create_user_service(
            username=body.username,
            email=body.email,
            password=body.password1
        )
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
        user_service: UserService = Depends(get_user_service)
) -> JSONResponse:
    """Controller that verifies email after registration"""

    try:
        await user_service.verify_email_service(token=token)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "The email was verified successfully"}
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Cannot verify email"}
        )


@user_router.get(path="/", response_model=ShowUserSchema)
async def get_user(user: User = Depends(get_current_user)) -> ShowUserSchema:
    """Controller that returns user data for profile"""

    return user


@user_router.delete(path="/")
async def delete_user(
        user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service)
) -> JSONResponse:
    """Controller that deactivates user"""

    await user_service.delete_user_service(user=user)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"The user deleted successfully"}
    )


@user_router.post(path="/auth/login", response_model=TokenSchema)
async def login(
        body: OAuth2PasswordRequestForm = Depends(),
        user_service: UserService = Depends(get_user_service)
) -> TokenSchema:
    """Controller for user authentication and authorization"""

    try:
        token_data: dict = await user_service.login_service(
            username=body.username,
            password=body.password
        )
        return TokenSchema(**token_data)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Incorrect username or password"}
        )


@user_router.post(path="/auth/refresh-token", response_model=TokenSchema)
async def refresh_token(
        user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service)
) -> TokenSchema:
    """Controller that refreshes access token"""

    token_data: dict = user_service.refresh_token_service(user=user)

    return TokenSchema(**token_data)


@user_router.patch(path='/change-username', response_model=ShowUserSchema)
async def change_username(
        body: ChangeUsernameSchema,
        user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service)
) -> ShowUserSchema:
    """Controller for username changing"""

    try:
        updated_user: User = await user_service.change_username_service(
            user=user,
            new_username=body.username
        )
        return updated_user

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this username already exists"
        )


@user_router.patch(path="/change-password", response_model=ShowUserSchema)
async def change_password(
        body: ChangePasswordSchema,
        user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service)
) -> ShowUserSchema:
    """Controller for password changing"""

    try:
        updated_user: User = await user_service.change_password_service(
            user=user,
            old_password=body.old_password,
            new_password=body.password1
        )
        return updated_user

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password was provided"
        )


@user_router.patch(path="/change-email")
async def change_email(
        body: EmailSchema,
        user: User = Depends(get_current_user),
        user_service: UserService = Depends(get_user_service)
) -> JSONResponse:
    """Controller that sends email to confirm the email change"""

    try:
        await user_service.change_email_service(
            new_email=body.email,
            user=user
        )
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


@user_router.get(path="/change-email/confirmation", response_model=ShowUserSchema)
async def confirm_email_change(
        token: str,
        user_service: UserService = Depends(get_user_service)
) -> ShowUserSchema:
    """Controller that changes email"""

    try:
        updated_user: User = await user_service.confirm_email_change_service(
            token=token
        )
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
async def reset_password(
        body: EmailSchema,
        user_service: UserService = Depends(get_user_service)
) -> JSONResponse:
    """Controller that sends email to confirm password reset"""

    try:
        await user_service.reset_password_service(email=body.email)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Password reset email was sent"}
        )

    except (SMTPRecipientsRefused, SMTPDataError):
        raise email_sending_exception


@user_router.patch(
    path="/auth/reset-password/confirmation",
    response_model=ShowUserSchema
)
async def change_password_on_reset(
        body: ResetPasswordSchema,
        user_service: UserService = Depends(get_user_service)
) -> ShowUserSchema:
    """Controller that changes password on reset"""

    try:
        updated_user: User = await user_service.change_password_on_reset_service(
            token=body.token,
            new_password=body.password1
        )
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
