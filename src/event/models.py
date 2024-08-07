import uuid
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.database import Base
from src.pet.models import Pet  # noqa


class Event(Base):
    """Model representing an event"""

    __tablename__ = "event"

    event_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(String(300), nullable=True)
    scheduled_at: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE ('utc', now())")
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE ('utc', now())"), onupdate=datetime.utcnow
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pet.pet_id"))
    is_happened: Mapped[bool] = mapped_column(default=False)

    pet = relationship("Pet", back_populates="events")

    def __repr__(self):
        return self.title

    def __eq__(self, other):
        return str(self.event_id) == str(other.event_id)


class TaskRecord(Base):
    """Models representing celery task associated with the event"""

    __tablename__ = "task_record"

    task_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID]

    def __repr__(self):
        return f"Task record №{self.task_id}"
