from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.infrastructure.redis import redis

app = FastAPI(
    title="Movies Storage",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)


@asynccontextmanager
async def startup_lifespan(app: FastAPI):
    redis.redis = Redis(host=settings.redis_host,
                        port=settings.redis_port, db=0, decode_responses=True)
    yield
    await redis.redis.close()

app.add_event_handler("startup", startup_lifespan)

app.include_router(api_router, prefix="/api/v1")
