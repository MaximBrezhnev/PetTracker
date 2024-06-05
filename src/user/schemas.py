from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from src.user.mixins import UsernameValidationMixin, PasswordValidationMixin


class CreateUserDTO(UsernameValidationMixin, PasswordValidationMixin, BaseModel):
    """Model that represents data for registration"""

    username: str
    email: EmailStr
    password1: str
    password2: str


class ShowUserDTO(BaseModel):
    """Model that represents data for user displaying"""

    model_config = ConfigDict(from_attributes=True)

    username: str
    email: EmailStr


class LoginDTO(BaseModel):
    """Model that represents data for logging"""

    email: EmailStr
    password: str


class TokenDTO(BaseModel):
    """Model that represents data for authorization"""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str


class ChangeUsernameDTO(UsernameValidationMixin, BaseModel):
    """Model that represents data for username change"""

    username: str


class ChangePasswordDTO(PasswordValidationMixin, BaseModel):
    """Model that represents data for password change"""

    old_password: str
    new_password1: str
    new_password2: str


class EmailDTO(BaseModel):
    """Model that represents data with password reset email"""

    email: EmailStr


class ResetPasswordDTO(PasswordValidationMixin, BaseModel):
    """Model that represents data for password reset"""

    token: str
    new_password1: str
    new_password2: str
