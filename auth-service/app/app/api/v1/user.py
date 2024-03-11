from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Body
from app.infrastructure.db.database import get_session
from app.schemas.user import UserGet, UserCreate, UserRoleUpdate
from app.schemas.role import RoleGet, RoleCreate, RoleUpdate
from app.core.config import settings
from app.auth.auth_helpers import get_current_session_user
from app.auth.role_helpers import role_required, set_user_role
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="v1/tokens")

router = APIRouter()

@router.post("/users/me", response_model=UserGet)
async def read_users_me(db: AsyncSession = Depends(get_session), token: str = Depends(OAUTH2_SCHEME)):
    active_user = await get_current_session_user(db, token)
    return active_user

@router.patch("/user_roles", response_model=UserCreate)
async def update_user_role_endpoint(
    user_data: UserRoleUpdate = Body(...),
    db: AsyncSession = Depends(get_session),
    _ = Depends(
        role_required(
        [settings.super_admin_role_name,
        settings.admin_role_name]
        )
    ),
):
    updated_user = await set_user_role(db, user_data.user_id, user_data.role_id)
    return updated_user

# @router.patch("/user", response_model=UserGet)
# async def update_login_and_password(
#     user_update: UserCreate = Body(...), 
#     current_user: UserGet = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     updated_user = await update_user_login_and_password(db, current_user.id, user_update, session_key)
#     if not updated_user:
#         raise HTTPException(status_code=400, detail="Unable to update user")
#     return updated_user
