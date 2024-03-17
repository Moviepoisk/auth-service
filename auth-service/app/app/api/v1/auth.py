from fastapi import APIRouter, Body, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_helpers import (
    authenticate_user,
    create_access_and_refresh_tokens,
    get_login_history,
    refresh_user_tokens,
    register_new_user,
    revoke_refresh_token,
)
from app.infrastructure.db.database import get_session
from app.schemas.auth import Tokens
from app.schemas.user import UserCreate
router = APIRouter()

OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="v1/tokens")
@router.post("/tokens", response_model=Tokens)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(
        db=db, email_or_login=form_data.username, password=form_data.password
    )
    tokens = await create_access_and_refresh_tokens(db=db, login=user.login)
    return tokens


@router.post("/login_history")
async def login_history(
    db: AsyncSession = Depends(get_session), token: str = Depends(OAUTH2_SCHEME)
):
    login_history = await get_login_history(db, token)
    return login_history


@router.post("/refresh")
async def refresh_access_and_refresh_tokens(
    refresh_token_str: str = Body(...), db: AsyncSession = Depends(get_session)
):
    tokens = await refresh_user_tokens(refresh_token_str, db)
    return tokens


@router.post("/signup")
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_session),
):
    new_user_id = await register_new_user(db, user_data)
    return new_user_id


@router.post("/logout")
async def user_logout(
    db: AsyncSession = Depends(get_session), token: str = Depends(OAUTH2_SCHEME)
):
    await revoke_refresh_token(db, token)
    return "Logged out successfully"
