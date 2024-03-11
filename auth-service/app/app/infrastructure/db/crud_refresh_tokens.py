# auth-service/app/app/infrastructure/db/crud_refresh_tokens.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.users import RefreshTokenDbModel
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.users import RefreshTokenDbModel
from datetime import datetime, timedelta
from app.core.config import settings


async def get_refresh_token_by_user_id_db(async_session: AsyncSession, user_id: uuid.UUID) -> RefreshTokenDbModel:
    result = await async_session.execute(select(RefreshTokenDbModel).where(RefreshTokenDbModel.user_id == user_id))
    token = result.scalars().first()
    return token


async def delete_all_refresh_tokens_by_user_id_db(async_session: AsyncSession, user_id: uuid.UUID) -> bool:
    result = await async_session.execute(select(RefreshTokenDbModel).where(RefreshTokenDbModel.user_id == user_id))
    tokens = result.scalars().all()
    if tokens:
        # В SQLAlchemy необходимо удалить каждый токен по отдельности
        for token in tokens:
            await async_session.delete(token)
        await async_session.commit()
        return True
    return False

async def create_refresh_token_db(async_session: AsyncSession, token: RefreshTokenDbModel) -> RefreshTokenDbModel:
    async_session.add(token)
    await async_session.commit()
    await async_session.refresh(token)
    return token


async def update_refresh_token_db(async_session: AsyncSession, token_id: uuid.UUID, **kwargs) -> RefreshTokenDbModel:
    result = await async_session.execute(select(RefreshTokenDbModel).where(RefreshTokenDbModel.id == token_id))
    token = result.scalars().first()
    if token:
        for key, value in kwargs.items():
            if hasattr(token, key):
                setattr(token, key, value)
        await async_session.commit()
        await async_session.refresh(token)
        return token
    else:
        return None
