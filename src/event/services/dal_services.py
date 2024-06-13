from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


async def create_event_in_database(
        title: str,
        content: Optional[str],
        pet_id: str,
        scheduled_at: datetime,
        db_session: AsyncSession
):
    async with db_session.begin():
        event = Event(
            title=body.title,
            content=body.content,
            scheduled_at=scheduled_at,
            pet_id=body.pet_id
        )
        db_session.add(event)
        await db_session.flush()