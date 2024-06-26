from aiosmtplib import SMTPDataError
from aiosmtplib import SMTPRecipientsRefused
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

from src.dependencies import get_current_user
from src.exceptions import email_sending_exception
from src.user.dependencies import get_user_service
from src.user.models import User
from src.user.schemas import ChangePasswordSchema
from src.user.schemas import ChangeUsernameSchema
from src.user.schemas import CreateUserSchema
from src.user.schemas import EmailSchema
from src.user.schemas import ResetPasswordSchema
from src.user.schemas import ShowUserSchema
from src.user.schemas import TokenSchema
from src.user.services.services import UserService


user_router: APIRouter = APIRouter(
    prefix="/user",
    tags=[
        "user",
    ],
)


@user_router.post(path="/")
async def create_user(
    body: CreateUserSchema, user_service: UserService = Depends(get_user_service)
) -> JSONResponse:
    """
    Endpoint that creates inactive user. If inactive user with this email exists,
    it updates username and password. Then it sends an activation email
    """

    try:
        await user_service.create_user(
            username=body.username, email=body.email, password=body.password1
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "confirmation email was sent"},
        )

    except (ValueError, IntegrityError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this credentials already exists",
        )

    except (SMTPRecipientsRefused, SMTPDataError):
        raise email_sending_exception


@user_router.patch(path="/verification")
async def verify_email(
    token: str, user_service: UserService = Depends(get_user_service)
) -> JSONResponse:
    """Endpoint that verifies email after registration"""

    try:
        await user_service.verify_email(token=token)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "The email was verified successfully"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot verify email"
        )


@user_router.get(path="/", response_model=ShowUserSchema)
async def get_user(user: User = Depends(get_current_user)) -> User:
    """Endpoint that returns user data for profile"""

    return user


@user_router.delete(path="/")
async def delete_user(
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> JSONResponse:
    """Endpoint that deactivates user"""

    await user_service.delete_user(user=user)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "The user deleted successfully"},
    )


@user_router.post(path="/auth/login", response_model=TokenSchema)
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
) -> TokenSchema:
    """Endpoint for user authentication and authorization"""

    try:
        token_data: dict = await user_service.login(
            username=body.username, password=body.password
        )
        return TokenSchema(**token_data)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )


@user_router.post(path="/auth/refresh-token", response_model=TokenSchema)
async def refresh_token(
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> TokenSchema:
    """Endpoint that refreshes access token"""

    token_data: dict = user_service.refresh_token(user=user)

    return TokenSchema(**token_data)


@user_router.patch(path="/change-username", response_model=ShowUserSchema)
async def change_username(
    body: ChangeUsernameSchema,
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Endpoint for username changing"""

    try:
        updated_user: User = await user_service.change_username(
            user=user, new_username=body.username
        )
        return updated_user

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this username already exists",
        )


@user_router.patch(path="/change-password", response_model=ShowUserSchema)
async def change_password(
    body: ChangePasswordSchema,
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Endpoint for password changing"""

    try:
        updated_user: User = await user_service.change_password(
            user=user, old_password=body.old_password, new_password=body.password1
        )
        return updated_user

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password was provided",
        )


@user_router.patch(path="/change-email")
async def change_email(
    body: EmailSchema,
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> JSONResponse:
    """Endpoint that sends email to confirm the email change"""

    try:
        await user_service.change_email(new_email=body.email, user=user)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Email for email change confirmation was sent"},
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user already uses this email",
        )

    except (SMTPRecipientsRefused, SMTPDataError):
        raise email_sending_exception


@user_router.patch(path="/change-email/confirmation", response_model=ShowUserSchema)
async def confirm_email_change(
    token: str, user_service: UserService = Depends(get_user_service)
) -> User:
    """Endpoint that changes email"""

    try:
        updated_user: User = await user_service.confirm_email_change(token=token)
        return updated_user

    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not validate credentials",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
        )


@user_router.post(path="/auth/reset-password")
async def reset_password(
    body: EmailSchema, user_service: UserService = Depends(get_user_service)
) -> JSONResponse:
    """Endpoint that sends email to confirm password reset"""

    try:
        await user_service.reset_password(email=body.email)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Password reset email was sent"},
        )

    except (SMTPRecipientsRefused, SMTPDataError):
        raise email_sending_exception


@user_router.patch(
    path="/auth/reset-password/confirmation", response_model=ShowUserSchema
)
async def change_password_on_reset(
    body: ResetPasswordSchema, user_service: UserService = Depends(get_user_service)
) -> User:
    """Endpoint that changes password on reset"""

    try:
        updated_user: User = await user_service.change_password_on_reset(
            token=body.token, new_password=body.password1
        )
        return updated_user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
        )
