from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.users import RefreshTokenDbModel


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
    def __init__(self, db: AsyncSession):
        self.db = db
        self.key_prefix_id = "refresh_token:user:id"

    async def create_refresh_token(
        self, user_id: UUID, token: str, expires_at: datetime
    ) -> None:
        refresh_token = RefreshTokenDbModel(
            user_id=user_id, token=token, expires_at=expires_at, revoked=False
        )
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)

        return refresh_token

    async def get_refresh_token_by_user_id(
        self, user_id: UUID
    ) -> Optional[RefreshTokenDbModel]:
        query = select(RefreshTokenDbModel).where(
            RefreshTokenDbModel.user_id == user_id,
            RefreshTokenDbModel.revoked is False
        )
        result = await self.db.execute(query)
        refresh_token = result.scalars().first()

        return refresh_token

    async def revoke_refresh_token(self, id: UUID) -> None:
        await self.db.execute(
            update(RefreshTokenDbModel)
            .where(RefreshTokenDbModel.id == id)
            .values(revoked=True)
        )
        await self.db.commit()

    async def delete_refresh_token(self, id: UUID) -> None:
        await self.db.execute(
            delete(RefreshTokenDbModel).where(
                RefreshTokenDbModel.user_id == id)
        )
        await self.db.commit()


class RefreshTokenRepositoryFactory:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_repository(self) -> AbstractRefreshTokenRepository:
        # Pass the session to the RefreshTokenRepository
        return RefreshTokenRepository(self.db)
