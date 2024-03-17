from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.users import EncryptionKeysModel
from app.infrastructure.redis.redis import get_redis
from app.infrastructure.redis.cache_manager import RedisCacheManager


class AbstractKeyStorageRepository(ABC):
    @abstractmethod
    async def save_keys(
        self,
        user_id: str,
        private_key: bytes,
        public_key: bytes,
        encrypted_session_key: bytes,
    ) -> None:
        pass

    @abstractmethod
    async def get_keys(self, user_id: UUID) -> Optional[EncryptionKeysModel]:
        pass

    @abstractmethod
    async def revoke_keys(self, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def delete_keys(self, user_id: UUID) -> None:
        pass


class KeyStorageRepository(AbstractKeyStorageRepository):
    def __init__(self, db: AsyncSession, cache_manager: RedisCacheManager):
        self.db = db
        self.cache_manager = cache_manager
        self.key_prefix_id = "encryption_keys:user:id"
    
    async def _set_cache(self, prefix_key, key, model_data: EncryptionKeysModel):
        data = model_data.to_dict() # перевод в формат для хранения в редис
        await self.cache_manager.set(f"{prefix_key}:{key}", data)
    
    async def _get_cache(self, prefix_key, key, model = EncryptionKeysModel):
        data = await self.cache_manager.get(f"{prefix_key}:{key}")
        if data:
            return model(**data) # перевод в модель
        return data
    
    async def _invalidate_cache(self, prefix_key, key):
        await self.cache_manager.delete(f"{prefix_key}:{key}")

    async def save_keys(
        self,
        user_id: UUID,
        private_key: bytes,
        public_key: bytes,
        encrypted_session_key: bytes,
    ) -> None:
        user_key = EncryptionKeysModel(
            user_id=user_id,
            private_key=private_key,
            public_key=public_key,
            encrypted_session_key=encrypted_session_key,
        )
        self.db.add(user_key)
        await self.db.commit()
        await self.db.refresh(user_key)
        await self._set_cache(prefix_key=self.key_prefix_id, key=user_key.id, model_data=user_key)
        return user_key

    async def get_keys(self, user_id: UUID) -> Optional[EncryptionKeysModel]:
        # блок кеширования
        cache = await self._get_cache(prefix_key=self.key_prefix_id, key=user_id)
        if cache:
            return cache
        
        result = await self.db.execute(
            select(EncryptionKeysModel).filter_by(user_id=user_id)
        )
        user_key = result.scalars().first()
        if user_key:
            await self._set_cache(prefix_key=self.key_prefix_id, key=user_key.id, model_data=user_key)
        return user_key

    async def revoke_keys(self, user_id: UUID) -> None:
        await self.db.execute(
            update(EncryptionKeysModel)
            .where(EncryptionKeysModel.user_id == user_id)
            .values(revoked=True)
        )
        await self.db.commit()
        await self._invalidate_cache(prefix_key=self.key_prefix_id, key=user_id)

    async def delete_keys(self, user_id: UUID) -> None:
        await self.db.execute(
            delete(EncryptionKeysModel).where(EncryptionKeysModel.user_id == user_id)
        )
        await self.db.commit()
        await self._invalidate_cache(prefix_key=self.key_prefix_id, key=user_id)


class KeyStorageRepositoryFactory:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_repository(self) -> AbstractKeyStorageRepository:
        # Асинхронное получение асинхронного клиента Redis
        redis_client = await get_redis()
        cache_manager = RedisCacheManager(redis=redis_client)

        return KeyStorageRepository(self.db, cache_manager=cache_manager)
