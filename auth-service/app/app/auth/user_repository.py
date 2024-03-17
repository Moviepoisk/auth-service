from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.users import UsersDbModel
from app.infrastructure.redis.redis import get_redis
from app.infrastructure.redis.cache_manager import RedisCacheManager


class AbstractUserRepository(ABC):
    @abstractmethod
    async def create_user(self, user_data: dict) -> UsersDbModel:
        pass

    @abstractmethod
    async def get_user_by_email_or_login(
        self, identifier: str
    ) -> Optional[UsersDbModel]:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> Optional[UsersDbModel]:
        pass

    @abstractmethod
    async def update_user(self, user_id: UUID, **kwargs) -> Optional[UsersDbModel]:
        pass

    @abstractmethod
    async def delete_user(self, user_id: UUID) -> bool:
        pass

    @abstractmethod
    async def list_users(self) -> List[UsersDbModel]:
        pass


class UserRepository(AbstractUserRepository):
    def __init__(self, db: AsyncSession, cache_manager: RedisCacheManager):
        self.db = db
        self.cache_manager = cache_manager


    async def _cache_user_data(self, user: UsersDbModel):
        """Кеширование данных пользователя."""
        user_data = user.to_dict()
        await self.cache_manager.set(f"user:id:{user.id}", user_data)
        await self.cache_manager.set(f"user:identifier:{user.email}", user_data)
        await self.cache_manager.set(f"user:identifier:{user.login}", user_data)

    async def _invalidate_user_cache(self, user: UsersDbModel):
        """Инвалидация кэша пользователя."""
        await self.cache_manager.delete(f"user:id:{user.id}")
        await self.cache_manager.delete(f"user:identifier:{user.email}")
        await self.cache_manager.delete(f"user:identifier:{user.login}")

    async def create_user(self, user_data: dict) -> UsersDbModel:
        new_user = UsersDbModel(**user_data)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        # блок кеширования
        await self._cache_user_data(new_user)
        return new_user


    async def get_user_by_email_or_login(
        self, identifier: str
    ) -> Optional[UsersDbModel]:
        
        # блок кеширования
        cached_value = await self.cache_manager.get(f"user:identifier:{identifier}")
        if cached_value:
            return UsersDbModel(**cached_value)

        query = select(UsersDbModel).where(
            (UsersDbModel.email == identifier) | (UsersDbModel.login == identifier)
        )
        result = await self.db.execute(query)
        user = result.scalars().first()
        
        # блок кеширования
        if user:
            await self._cache_user_data(user)

        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[UsersDbModel]:
        # блок кеширования
        cached_value = await self.cache_manager.get(f"user:id:{user_id}")
        if cached_value:
            return UsersDbModel(**cached_value)

        query = select(UsersDbModel).where(UsersDbModel.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()

        # блок кеширования
        if user:
            await self._cache_user_data(user)

        return user

    async def update_user(self, user_id: UUID, **kwargs) -> Optional[UsersDbModel]:
        query = select(UsersDbModel).where(UsersDbModel.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        
        # блок кеширования
        await self._invalidate_user_cache(user)

        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            await self.db.commit()

            # блок кеширования
            await self._cache_user_data(user)
            
            return user
        return None

    async def delete_user(self, user_id: UUID) -> bool:
        query = select(UsersDbModel).where(UsersDbModel.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        if user:
            await self.db.delete(user)
            await self.db.commit()
            
            # блок кеширования
            await self._invalidate_user_cache(user)

            return True
        return False

    async def list_users(self) -> List[UsersDbModel]:
        query = select(UsersDbModel)
        result = await self.db.execute(query)
        users = result.scalars().all()
        return users


class UserRepositoryFactory:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_repository(self) -> AbstractUserRepository:
        # Асинхронное получение асинхронного клиента Redis
        redis_client = await get_redis()
        cache_manager = RedisCacheManager(redis=redis_client)
        # Pass the session to the UserRepository
        return UserRepository(self.db, cache_manager=cache_manager)
