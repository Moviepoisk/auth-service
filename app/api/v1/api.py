from fastapi import APIRouter

from app.api.v1.endpoints import auth, role, user

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(role.router, tags=["role"])
api_router.include_router(user.router, tags=["user"])
