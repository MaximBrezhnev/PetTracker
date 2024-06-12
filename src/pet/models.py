import datetime
from enum import Enum
import uuid

from sqlalchemy import String, Enum as SQLAlchemyEnum, ForeignKey, text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.user.models import User  # noqa


class PetGenderEnum(str, Enum):
    male = "male"
    female = "female"


class Pet(Base):
    """Model that represents a pet"""

    __tablename__ = "pet"

    pet_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(30))
    species: Mapped[str] = mapped_column(String(30))
    breed: Mapped[str] = mapped_column(String(30), nullable=True)
    gender: Mapped[str] = mapped_column(SQLAlchemyEnum(PetGenderEnum))
    weight: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("TIMEZONE ('utc', now())")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=text("TIMEZONE ('utc', now())"),
        onupdate=datetime.datetime.utcnow
    )
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("user.user_id"))

    owner = relationship("User", back_populates="pets")
    events = relationship("Event", back_populates="pet")

    def __repr__(self):
        return self.name


