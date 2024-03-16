from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_helpers import (
    get_current_session_user,
    update_user_login_and_password,
)
from app.auth.role_helpers import role_required, set_user_role
from app.core.config import settings
from app.infrastructure.db.database import get_session
from app.schemas.user import (
    UserCreate,
    UserGet,
    UserRoleUpdate,
    UserLoginPasswordUpdate,
)

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="v1/tokens")

router = APIRouter()


@router.post("/user/me", response_model=UserGet)
async def read_users_me(
    db: AsyncSession = Depends(get_session), token: str = Depends(OAUTH2_SCHEME)
):
    active_user = await get_current_session_user(db, token)
    return active_user


@router.patch("/user/roles", response_model=UserCreate)
async def update_user_role_endpoint(
    user_data: UserRoleUpdate = Body(...),
    db: AsyncSession = Depends(get_session),
    _=Depends(
        role_required([settings.super_admin_role_name, settings.admin_role_name])
    ),
):
    updated_user = await set_user_role(db, user_data.user_id, user_data.role_id)
    return updated_user


@router.patch("/user")  # , response_model=UserGet)
async def update_login_and_password(
    user_update: UserLoginPasswordUpdate = Body(...),
    db: AsyncSession = Depends(get_session),
    token: str = Depends(OAUTH2_SCHEME),
):
    # Обновление логина и пароля пользователя
    updated_user = await update_user_login_and_password(db, user_update, token)
    return updated_user
