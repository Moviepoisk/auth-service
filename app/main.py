from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(title='Moviepoisk Auth')


@app.get("/", status_code=200)
def read_root():
    print(settings)
    return {"Hello": "World"}


app.include_router(api_router, prefix="/api/v1")
