from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.users import UsersDbModel


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
    def __init__(self, db: AsyncSession):
        self.db = db

    # Update all method implementations to use self.db instead of db_session
    async def create_user(self, user_data: dict) -> UsersDbModel:
        new_user = UsersDbModel(**user_data)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def get_user_by_email_or_login(
        self, identifier: str
    ) -> Optional[UsersDbModel]:
        query = select(UsersDbModel).where(
            (UsersDbModel.email == identifier) | (UsersDbModel.login == identifier)
        )
        result = await self.db.execute(query)
        user = result.scalars().first()
        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[UsersDbModel]:
        query = select(UsersDbModel).where(UsersDbModel.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        return user

    async def update_user(self, user_id: UUID, **kwargs) -> Optional[UsersDbModel]:
        query = select(UsersDbModel).where(UsersDbModel.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            await self.db.commit()
            return user
        return None

    async def delete_user(self, user_id: UUID) -> bool:
        query = select(UsersDbModel).where(UsersDbModel.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        if user:
            await self.db.delete(user)
            await self.db.commit()
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

    def get_repository(self) -> AbstractUserRepository:
        # Pass the session to the UserRepository
        return UserRepository(self.db)
