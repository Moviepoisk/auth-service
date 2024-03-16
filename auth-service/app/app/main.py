from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from app.api.v1.api import api_router
from app.auth.init import create_roles, create_superuser
from app.core.config import settings
from app.infrastructure.db.database import async_session
from app.infrastructure.redis import redis

app = FastAPI(
    title="Movies Storage",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.on_event("startup")
async def startup():
    async with async_session() as db:  # Предполагается, что async_session это ваша функция получения сессии
        await create_roles(db)
        await create_superuser(db)

    redis.redis = Redis(host=settings.redis_host, port=settings.redis_port)


@app.on_event("shutdown")
async def shutdown():
    await redis.redis.close()


app.include_router(api_router, prefix="/api/v1")
