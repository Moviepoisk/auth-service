from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.users import RefreshTokenDbModel
from app.infrastructure.redis.redis import get_redis
from app.infrastructure.redis.cache_manager import RedisCacheManager


class AbstractRefreshTokenRepository(ABC):
    @abstractmethod
    async def create_refresh_token(
        self, user_id: UUID, token: str, expires_at: datetime
    ) -> None:
        """Creates a new refresh token."""
        pass

    @abstractmethod
    async def get_refresh_token_by_user_id(
        self, user_id: UUID
    ) -> Optional[RefreshTokenDbModel]:
        """Retrieves a refresh token by its token value."""
        pass

    @abstractmethod
    async def revoke_refresh_token(self, id: UUID) -> None:
        """Revokes a refresh token."""
        pass

    @abstractmethod
    async def delete_refresh_token(self, id: UUID) -> None:
        """Deletes a refresh token."""
        pass


class RefreshTokenRepository(AbstractRefreshTokenRepository):
    def __init__(self, db: AsyncSession, cache_manager: RedisCacheManager):
        self.db = db
        self.cache_manager = cache_manager
        self.key_prefix_id = "refresh_token:user:id"

    async def _set_cache(self, prefix_key, key, model_data: RefreshTokenDbModel):
        data = model_data.to_dict() # перевод в формат для хранения в редис
        await self.cache_manager.set(f"{prefix_key}:{key}", data)
    
    async def _get_cache(self, prefix_key, key, model = RefreshTokenDbModel):
        data = await self.cache_manager.get(f"{prefix_key}:{key}")
        if data:
            return model(**data) # перевод в модель
        return data
    
    async def _invalidate_cache(self, prefix_key, key):
        await self.cache_manager.delete(f"{prefix_key}:{key}")

    async def create_refresh_token(
        self, user_id: UUID, token: str, expires_at: datetime
    ) -> None:
        refresh_token = RefreshTokenDbModel(
            user_id=user_id, token=token, expires_at=expires_at, revoked=False
        )
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)

        await self._set_cache(prefix_key=self.key_prefix_id, key=user_id, model_data=refresh_token)

        return refresh_token

    async def get_refresh_token_by_user_id(
        self, user_id: UUID
    ) -> Optional[RefreshTokenDbModel]:
        # блок кеширования
        cached_value = await self._get_cache(prefix_key=self.key_prefix_id, key=user_id)
        if cached_value:
            return cached_value
        
        query = select(RefreshTokenDbModel).where(
            RefreshTokenDbModel.user_id == user_id, RefreshTokenDbModel.revoked == False
        )
        result = await self.db.execute(query)
        refresh_token = result.scalars().first()

        if refresh_token:
            await self._set_cache(prefix_key=self.key_prefix_id, key=user_id, model_data=refresh_token)

        return refresh_token

    async def revoke_refresh_token(self, id: UUID) -> None:
        await self.db.execute(
            update(RefreshTokenDbModel)
            .where(RefreshTokenDbModel.id == id)
            .values(revoked=True)
        )
        await self._invalidate_cache(prefix_key=self.key_prefix_id, key=id)
        await self.db.commit()

    async def delete_refresh_token(self, id: UUID) -> None:
        await self.db.execute(
            delete(RefreshTokenDbModel).where(RefreshTokenDbModel.user_id == id)
        )
        await self._invalidate_cache(prefix_key=self.key_prefix_id, key=id)
        await self.db.commit()


class RefreshTokenRepositoryFactory:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_repository(self) -> AbstractRefreshTokenRepository:
        # Асинхронное получение асинхронного клиента Redis
        redis_client = await get_redis()
        cache_manager = RedisCacheManager(redis=redis_client)

        # Pass the session to the RefreshTokenRepository
        return RefreshTokenRepository(self.db, cache_manager=cache_manager)
