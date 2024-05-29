import uvicorn
from fastapi import FastAPI, APIRouter

from src.user.controllers import user_router


app = FastAPI(title="PetTracker")


main_router = APIRouter(prefix="/api/v1")
main_router.include_router(user_router)

app.include_router(main_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=18000)
