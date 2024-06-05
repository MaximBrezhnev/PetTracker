import datetime
import uuid
from uuid import UUID

from sqlalchemy import text, String
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    """Models that represents user"""

    __tablename__ = "user"

    user_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("TIMEZONE ('utc', now())")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("TIMEZONE ('utc', now())"),
        onupdate=datetime.datetime.utcnow
    )
    is_active: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        return self.username

