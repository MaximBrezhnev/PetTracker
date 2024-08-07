from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session
from src.pet.services.dal import PetDAL
from src.pet.services.services import PetService


def get_pet_service(db_session: AsyncSession = Depends(get_db_session)) -> PetService:
    """Dependence that creates PetService object using
    session object from get_db_session dependence and PetDAL service"""

    return PetService(db_session=db_session, dal_class=PetDAL)
