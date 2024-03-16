from abc import ABC, abstractmethod
from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.users import LoginHistoryDbModel


# Abstract Repository for Login History Operations
class AbstractLoginHistoryRepository(ABC):
    @abstractmethod
    async def create_login_history(
        self, user_id: UUID, ip: str, user_agent: str
    ) -> LoginHistoryDbModel:
        pass

    @abstractmethod
    async def get_login_history_by_user_id(
        self, user_id: UUID
    ) -> List[LoginHistoryDbModel]:
        pass


# Concrete Repository Implementation for Login History Operations
class LoginHistoryRepository(AbstractLoginHistoryRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_login_history(
        self, user_id: UUID, ip: str, user_agent: str
    ) -> LoginHistoryDbModel:
        login_history = LoginHistoryDbModel(
            user_id=user_id, ip=ip, user_agent=user_agent
        )
        self.db.add(login_history)
        await self.db.commit()
        await self.db.refresh(login_history)
        return login_history

    async def get_login_history_by_user_id(
        self, user_id: UUID
    ) -> List[LoginHistoryDbModel]:
        result = await self.db.execute(
            select(LoginHistoryDbModel).where(LoginHistoryDbModel.user_id == user_id)
        )
        return result.scalars().all()


# Factory for Login History Repository
class LoginHistoryRepositoryFactory:
    def __init__(self, db: AsyncSession):
        self.db = db

    def get_repository(self) -> AbstractLoginHistoryRepository:
        return LoginHistoryRepository(self.db)
