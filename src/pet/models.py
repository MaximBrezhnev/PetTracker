import datetime
import uuid
from enum import Enum

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database import Base
from src.user.models import User  # noqa


class PetGenderEnum(str, Enum):
    """Enum class that represents options of pet gender"""

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
        onupdate=datetime.datetime.utcnow,
    )
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("user.user_id"))

    owner = relationship("User", back_populates="pets")
    events = relationship("Event", back_populates="pet")

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return str(self.pet_id) == str(other.pet_id)
