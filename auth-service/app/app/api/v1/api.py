from fastapi import APIRouter

from app.api.v1 import auth
from app.api.v1 import role
from app.api.v1 import user

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(role.router, tags=["role"])
api_router.include_router(user.router, tags=["user"])
