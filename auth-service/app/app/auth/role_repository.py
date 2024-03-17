import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.users import RoleDbModel, UsersDbModel
from app.infrastructure.redis.redis import get_redis
from app.infrastructure.redis.cache_manager import RedisCacheManager


# Abstract Repository for Role Operations
class AbstractRoleRepository(ABC):
    @abstractmethod
    async def create_role(self, name: str, description: str) -> RoleDbModel:
        pass

    @abstractmethod
    async def get_role_by_id(self, role_id: uuid.UUID) -> Optional[RoleDbModel]:
        pass

    @abstractmethod
    async def get_role_by_name(self, name: str) -> Optional[RoleDbModel]:
        pass

    @abstractmethod
    async def update_role(self, role_id: uuid.UUID, **kwargs) -> Optional[RoleDbModel]:
        pass

    @abstractmethod
    async def delete_role(self, role_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def get_role_by_user_id(self, user_id: uuid.UUID) -> Optional[RoleDbModel]:
        pass

    @abstractmethod
    async def get_all_roles(self) -> List[RoleDbModel]:
        pass


# Concrete Repository Implementation for Role Operations
class RoleRepository(AbstractRoleRepository):
    def __init__(self, db: AsyncSession, cache_manager: RedisCacheManager):
        self.db = db
        self.cache_manager = cache_manager
    
    async def _set_cache(self, prefix_key, key, model_data: RoleDbModel):
        data = model_data.to_dict() # перевод в формат для хранения в редис
        await self.cache_manager.set(f"{prefix_key}:{key}", data)
    
    async def _get_cache(self, prefix_key, key, model = RoleDbModel):
        data = await self.cache_manager.get(f"{prefix_key}:{key}")
        if data:
            return model(**data) # перевод в модель
        return data
    
    async def _invalidate_cache(self, prefix_key, key):
        await self.cache_manager.delete(f"{prefix_key}:{key}")


    async def create_role(self, name: str, description: str) -> RoleDbModel:
        role = RoleDbModel(name=name, description=description)
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        # cache
        await self._set_cache(prefix_key="role:id", key=role.id, model_data=role)
        await self._set_cache(prefix_key="role:name", key=role.name, model_data=role)
        return role


    async def get_role_by_id(self, role_id: uuid.UUID) -> Optional[RoleDbModel]:
        cache = await self._get_cache(prefix_key="role:id", key=role_id)
        if cache:
            return cache
        
        result = await self.db.execute(
            select(RoleDbModel).where(RoleDbModel.id == role_id)
        )
        role = result.scalars().first()
        if role:
            # кешируем роли
            await self._set_cache(prefix_key="role:id", key=role.id, model_data=role)
            await self._set_cache(prefix_key="role:name", key=role.name, model_data=role)
            return role

        return None

    async def get_role_by_name(self, name: str) -> Optional[RoleDbModel]:
        cache = await self._get_cache(prefix_key="role:name", key=name)
        if cache:
            return cache
        
        result = await self.db.execute(
            select(RoleDbModel).where(RoleDbModel.name == name)
        )
        role = result.scalars().first()
        # кешируем роли
        await self._set_cache(prefix_key="role:id", key=role.id, model_data=role)
        await self._set_cache(prefix_key="role:name", key=role.name, model_data=role)

        return role

    async def update_role(self, role_id: uuid.UUID, **kwargs) -> Optional[RoleDbModel]:
        result = await self.db.execute(
            select(RoleDbModel).where(RoleDbModel.id == role_id)
        )
        role = result.scalars().first()
        if role:
            for key, value in kwargs.items():
                setattr(role, key, value)
            await self.db.commit()

            await self.cache_manager.set(prefix_key="role:id", key=role.id, model_data=role)
            await self.cache_manager.set(prefix_key="role:name", key=role.name, model_data=role)  

            return role
        return None

    async def delete_role(self, role_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(RoleDbModel).where(RoleDbModel.id == role_id)
        )
        role = result.scalars().first()
        if role:
            await self.db.delete(role)
            await self.db.commit()
            await self.cache_manager.delete(prefix_key="role:id", key=role.id)
            await self.cache_manager.delete(prefix_key="role:name", key=role.name)
            return True
        return False

    async def get_role_by_user_id(self, user_id: uuid.UUID) -> Optional[RoleDbModel]:
        # TODO : кеширование пользователя
        
        result = await self.db.execute(
            select(UsersDbModel).where(UsersDbModel.id == user_id)
        )
        user = result.scalars().first()
        
        if user and user.role_id:
            cache = await self._get_cache(prefix_key="role:id", key=user.role_id)
        if cache:
                return cache
        
        if user and user.role_id:
            role_result = await self.db.execute(
                select(RoleDbModel).where(RoleDbModel.id == user.role_id)
            )
            role = role_result.scalars().first()
            # кешируем роли
            await self._set_cache(prefix_key="role:id", key=role.id, model_data=role)
            await self._set_cache(prefix_key="role:name", key=role.name, model_data=role)
            return role
        return None

    async def get_all_roles(self) -> List[RoleDbModel]:
        result = await self.db.execute(select(RoleDbModel))
        return result.scalars().all()


# Factory for Role Repository
class RoleRepositoryFactory:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_repository(self) -> AbstractRoleRepository:
        redis_client = await get_redis()
        cache_manager = RedisCacheManager(redis=redis_client)
        return RoleRepository(self.db, cache_manager=cache_manager)
