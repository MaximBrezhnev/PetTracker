import uvicorn
from fastapi import FastAPI

from src.router import main_router

app = FastAPI(title="PetTracker")

app.include_router(main_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
