from fastapi.routing import APIRouter

from src.user.controllers import user_router

main_router = APIRouter(prefix="/api/v1")
main_router.include_router(user_router)
