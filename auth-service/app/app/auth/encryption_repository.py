from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy import update, delete
from app.models.users import EncryptionKeysModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


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
    async def get_keys(self, user_id: str) -> Optional[EncryptionKeysModel]:
        pass

    @abstractmethod
    async def revoke_keys(self, user_id: str) -> None:
        pass

    @abstractmethod
    async def delete_keys(self, user_id: str) -> None:
        pass


class KeyStorageRepository(AbstractKeyStorageRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_keys(
        self,
        user_id: str,
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
        return user_key

    async def get_keys(self, user_id: str) -> Optional[EncryptionKeysModel]:
        result = await self.db.execute(
            select(EncryptionKeysModel).filter_by(user_id=user_id)
        )
        user_key = result.scalars().first()
        return user_key

    async def revoke_keys(self, user_id: str) -> None:
        await self.db.execute(
            update(EncryptionKeysModel)
            .where(EncryptionKeysModel.user_id == user_id)
            .values(revoked=True)
        )
        await self.db.commit()

    async def delete_keys(self, user_id: str) -> None:
        await self.db.execute(
            delete(EncryptionKeysModel).where(EncryptionKeysModel.user_id == user_id)
        )
        await self.db.commit()


class KeyStorageRepositoryFactory:
    def __init__(self, db: AsyncSession):
        self.db = db

    def get_repository(self) -> AbstractKeyStorageRepository:
        return KeyStorageRepository(self.db)
