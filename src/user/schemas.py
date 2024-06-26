from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr

from src.user.schema_mixins import PasswordValidationMixin
from src.user.schema_mixins import UsernameValidationMixin


class CreateUserSchema(UsernameValidationMixin, PasswordValidationMixin, BaseModel):
    """Schema that represents data for registration"""

    username: str
    email: EmailStr
    password1: str
    password2: str


class ShowUserSchema(BaseModel):
    """Schema that represents data for user displaying"""

    model_config = ConfigDict(from_attributes=True)

    username: str
    email: EmailStr


class TokenSchema(BaseModel):
    """Schema that represents data for authorization"""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str


class ChangeUsernameSchema(UsernameValidationMixin, BaseModel):
    """Schema that represents data for username change"""

    username: str


class ChangePasswordSchema(PasswordValidationMixin, BaseModel):
    """Schema that represents data for password change"""

    old_password: str
    password1: str
    password2: str


class EmailSchema(BaseModel):
    """Schema that represents data with password reset email"""

    email: EmailStr


class ResetPasswordSchema(PasswordValidationMixin, BaseModel):
    """Schema that represents data for password reset"""

    token: str
    password1: str
    password2: str
