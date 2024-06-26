from passlib.context import CryptContext

from src.config import project_settings


class Hasher:
    """Class that enables to work with password hashing"""

    def __init__(self):
        """Configures the schema of password hashing"""

        self.pwd_context: CryptContext = CryptContext(
            schemes=[
                project_settings.PWD_SCHEMA,
            ],
            deprecated=project_settings.PWD_DEPRECATED,
        )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Checks whether the provided password matches the hashed one"""

        return self.pwd_context.verify(hashed_password, plain_password)

    def get_password_hash(self, password: str) -> str:
        """Gets the hash of the provided password"""

        return self.pwd_context.hash(password)
