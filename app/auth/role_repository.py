import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.users import RoleDbModel, UsersDbModel


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
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_role(self, name: str, description: str) -> RoleDbModel:
        role = RoleDbModel(name=name, description=description)
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def get_role_by_id(self, role_id: uuid.UUID) -> Optional[RoleDbModel]:
        result = await self.db.execute(
            select(RoleDbModel).where(RoleDbModel.id == role_id)
        )
        role = result.scalars().first()
        if role:
            return role
        return None

    async def get_role_by_name(self, name: str) -> Optional[RoleDbModel]:
        result = await self.db.execute(
            select(RoleDbModel).where(RoleDbModel.name1 == name)
        )
        role = result.scalars().first()

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
            return True
        return False

    async def get_role_by_user_id(self, user_id: uuid.UUID) -> Optional[RoleDbModel]:
        result = await self.db.execute(
            select(UsersDbModel).where(UsersDbModel.id == user_id)
        )
        user = result.scalars().first()

        if user and user.role_id:
            role_result = await self.db.execute(
                select(RoleDbModel).where(RoleDbModel.id == user.role_id)
            )
            role = role_result.scalars().first()
            # кешируем роли
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
        return RoleRepository(self.db)
