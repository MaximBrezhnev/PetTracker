import uvicorn
from fastapi import APIRouter
from fastapi import FastAPI

from src.config import project_settings
from src.event.routes import event_router
from src.pet.routes import pet_router
from src.user.routes import user_router


app = FastAPI(title=project_settings.APP_TITLE)


main_router = APIRouter(prefix=project_settings.API_URL_PREFIX)
main_router.include_router(user_router)
main_router.include_router(pet_router)
main_router.include_router(event_router)
app.include_router(main_router)


if __name__ == "__main__":
    uvicorn.run(app=app, host=project_settings.APP_HOST, port=project_settings.APP_PORT)
