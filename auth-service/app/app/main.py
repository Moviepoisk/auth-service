from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from app.api.v1.api import api_router
from app.auth.init import create_roles, create_superuser
from app.core.config import settings
from app.infrastructure.db.database import async_session
from app.infrastructure.redis import redis
from app.schemas.role import RoleCreate


app = FastAPI(
    title="Movies Storage",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)

roles = [
        RoleCreate(
            name=settings.super_admin_role_name,
            description=settings.super_admin_role_description,
        ),
        RoleCreate(
            name=settings.admin_role_name, description=settings.admin_role_description
        ),
        RoleCreate(
            name=settings.user_role_name, description=settings.user_role_description
        ),
        RoleCreate(
            name=settings.subscriber_role_name,
            description=settings.subscriber_role_description,
        ),
        RoleCreate(
            name=settings.guest_role_name, description=settings.guest_role_description
        ),
    ]
@app.on_event("startup")
async def startup():
    redis.redis = Redis(host=settings.redis_host, port=settings.redis_port, db=0, decode_responses=True)
    async with async_session() as db:
        await create_roles(db, roles)
        await create_superuser(db)
    


@app.on_event("shutdown")
async def shutdown():
    await redis.redis.close()


app.include_router(api_router, prefix="/api/v1")
