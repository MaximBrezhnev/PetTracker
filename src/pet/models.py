import datetime
from enum import Enum
import uuid

from sqlalchemy import String, Enum as SQLAlchemyEnum, Table, Column, Integer, ForeignKey, text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


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
    owners = relationship("User", secondary="pet_user", back_populates="pets")

    def __repr__(self):
        return self.name


pet_user = Table(
    "pet_user",
    Base.metadata,
    Column(
        "user_id",
        UUID,
        ForeignKey("user.user_id"),
        primary_key=True
    ),
    Column(
        "pet_id",
        UUID,
        ForeignKey("pet.pet_id"),
        primary_key=True
    )
)

