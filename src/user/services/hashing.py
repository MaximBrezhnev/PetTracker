from passlib.context import CryptContext

from src.config2 import project_settings


class Hasher:
    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=[project_settings.PWD_SCHEMA, ],
            deprecated=project_settings.PWD_DEPRECATED
        )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)
