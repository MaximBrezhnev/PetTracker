import re
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

# Подумать над использованием orm_mode


LETTER_MATCH_PATTERN = re.compile(r"^[0-9а-яА-Яa-zA-Z\-_ ]+$")


class CreateUserDTO(BaseModel):
    username: str
    email: EmailStr = Field(max_length=50)
    password1: str
    password2: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, username: str) -> str:
        if len(username) < 1 or len(username) > 20:
            raise ValueError("Incorrect username length")
        if not LETTER_MATCH_PATTERN.match(username):
            raise ValueError("Username contains incorrect symbols")
        return username


    @field_validator("password1")
    @classmethod
    def validate_password(cls, password: str) -> str:
        if len(password) < 4:
            raise ValueError("Password is weak")
        return password

    @model_validator(mode="before")
    @classmethod
    def check_password_match(cls, data: dict) -> dict:
        if data["password1"] != data["password2"]:
            raise ValueError('passwords do not match')
        return data


class ShowUserDTO(BaseModel):
    user_id: UUID
    username: str
    email: EmailStr


class UpdateUserDTO(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = Field(max_length=50, default=None)

    @field_validator("username")
    @classmethod
    def validate_username(cls, username: str) -> str:
        if username is not None:
            if len(username) < 1 or len(username) > 20:
                raise ValueError("Incorrect username length")
            if not LETTER_MATCH_PATTERN.match(username):
                raise ValueError("Username contains incorrect symbols")
        return username


class LoginDTO(BaseModel):
    email: EmailStr
    password: str


class TokenDTO(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
