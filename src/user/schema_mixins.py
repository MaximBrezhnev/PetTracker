import re
from typing import ClassVar

from pydantic import field_validator
from pydantic import model_validator


class UsernameValidationMixin:
    """Mixin for the username validation"""

    LETTER_MATCH_PATTERN: ClassVar[re.Pattern] = re.compile(r"^[0-9а-яА-Яa-zA-Z\-_ ]+$")
    MIN_USERNAME_LENGTH: ClassVar[int] = 1
    MAX_USERNAME_LENGTH: ClassVar[int] = 20

    @field_validator("username", check_fields=False)
    @classmethod
    def validate_username(cls, username: str) -> str:
        """Checks if providing username contains the correct characters and has the correct length"""

        if (
            len(username) < cls.MIN_USERNAME_LENGTH
            or len(username) > cls.MAX_USERNAME_LENGTH
        ):
            raise ValueError("Incorrect username length")

        if not cls.LETTER_MATCH_PATTERN.match(username):
            raise ValueError("The username contains incorrect symbols")

        return username


class PasswordValidationMixin:
    """Mixin that checks that providing passwords match and they have the correct length"""

    MIN_PASSWORD_LENGTH: ClassVar[int] = 4

    @field_validator("password1", check_fields=False)
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Checks if the password has the correct length"""

        if len(password) < cls.MIN_PASSWORD_LENGTH:
            raise ValueError("The password is weak")

        return password

    @model_validator(mode="before")
    @classmethod
    def check_password_match(cls, data: dict) -> dict:
        """Checks if the passwords match"""

        if data.get("password1") != data.get("password2"):
            raise ValueError("The passwords do not match")

        return data
