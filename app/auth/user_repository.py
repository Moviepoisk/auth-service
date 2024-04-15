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
        self.key_prefix_id = "user:id"
        self.key_prefix_identifier = "user:identifier"

    async def _set_cache(self, prefix_key, key, model_data: UsersDbModel):
        data = model_data.to_dict()  # перевод в формат для хранения в редис
        await self.cache_manager.set(f"{prefix_key}:{key}", data)

    async def _get_cache(self, prefix_key, key, model=UsersDbModel):
        data = await self.cache_manager.get(f"{prefix_key}:{key}")
        if data:
            return model(**data)  # перевод в модель
        return data

    async def _invalidate_cache(self, prefix_key, key):
        await self.cache_manager.delete(f"{prefix_key}:{key}")

    async def create_user(self, user_data: dict) -> UsersDbModel:
        new_user = UsersDbModel(**user_data)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        # блок кеширования
        await self._set_cache(prefix_key=self.key_prefix_id, key=new_user.id, model_data=new_user)
        await self._set_cache(
            prefix_key=self.key_prefix_identifier, key=new_user.email, model_data=new_user
        )
        await self._set_cache(
            prefix_key=self.key_prefix_identifier, key=new_user.login, model_data=new_user
        )
        return new_user

    async def get_user_by_email_or_login(
        self, identifier: str
    ) -> Optional[UsersDbModel]:

        # блок кеширования
        cache = await self._get_cache(
            prefix_key=self.key_prefix_identifier, key=identifier
        )
        if cache:
            return cache

        query = select(UsersDbModel).where(
            (UsersDbModel.email == identifier) | (
                UsersDbModel.login == identifier)
        )
        result = await self.db.execute(query)
        user = result.scalars().first()

        # блок кеширования
        if user:
            await self._set_cache(
                prefix_key=self.key_prefix_id, key=user.id, model_data=user
            )
            await self._set_cache(
                prefix_key=self.key_prefix_identifier, key=user.email, model_data=user
            )
            await self._set_cache(
                prefix_key=self.key_prefix_identifier, key=user.login, model_data=user
            )
            return user

        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[UsersDbModel]:
        # блок кеширования
        cache = await self._get_cache(
            prefix_key=self.key_prefix_id, key=user_id
        )
        if cache:
            return cache

        query = select(UsersDbModel).where(UsersDbModel.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()

        # блок кеширования
        if user:
            await self._set_cache(
                prefix_key=self.key_prefix_id, key=user.id, model_data=user
            )
            await self._set_cache(
                prefix_key=self.key_prefix_identifier, key=user.email, model_data=user
            )
            await self._set_cache(
                prefix_key=self.key_prefix_identifier, key=user.login, model_data=user
            )

        return user

    async def update_user(self, user_id: UUID, **kwargs) -> Optional[UsersDbModel]:
        query = select(UsersDbModel).where(UsersDbModel.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()

        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            await self.db.commit()

            # блок кеширования
            await self._set_cache(prefix_key=self.key_prefix_id, key=user.id, model_data=user)
            await self._set_cache(prefix_key=self.key_prefix_identifier, key=user.email, model_data=user)
            await self._set_cache(prefix_key=self.key_prefix_identifier, key=user.login, model_data=user)

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
            await self._invalidate_cache(prefix_key=self.key_prefix_id, key=user_id)
            await self._invalidate_cache(prefix_key=self.key_prefix_identifier, key=user.email)
            await self._invalidate_cache(prefix_key=self.key_prefix_identifier, key=user.login)

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
