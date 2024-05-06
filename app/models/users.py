import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    LargeBinary,
    MetaData,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class RoleDbModel(Base):
    __tablename__ = "roles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name1,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }


class UsersDbModel(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    login = Column(String(255), nullable=False, unique=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=True
    )
    role = relationship("RoleDbModel", back_populates="users")
    login_histories = relationship(
        "LoginHistoryDbModel", back_populates="user")

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "login": self.login,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "encrypted_password": self.encrypted_password,
            "created_at": self.created_at.isoformat(),
            "role_id": str(self.role_id) if self.role_id else None,
        }


class LoginHistoryDbModel(Base):
    __tablename__ = "login_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False)
    ip = Column(String(255), nullable=False)
    user_agent = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("UsersDbModel", back_populates="login_histories")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "ip": self.ip,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
        }


class RefreshTokenDbModel(Base):
    __tablename__ = "refresh_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(Text, nullable=False, unique=True)  # Сам refresh токен
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False)
    expires_at = Column(
        DateTime, nullable=False
    )  # Время истечения срока действия токена
    # Время создания токена
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Boolean, default=False)  # Статус отзыва токена
    user = relationship("UsersDbModel", back_populates="refresh_tokens")

    def to_dict(self):
        return {
            "id": str(self.id),
            "token": self.token,
            "user_id": str(self.user_id),
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "revoked": self.revoked,
        }


class EncryptionKeysModel(Base):
    __tablename__ = "encryption_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    private_key = Column(LargeBinary, nullable=False)
    public_key = Column(LargeBinary, nullable=False)
    encrypted_session_key = Column(LargeBinary, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to the UsersDbModel to access the user information
    user = relationship("UsersDbModel", back_populates="encryption_keys")

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "private_key": self.private_key,
            "public_key": self.public_key,
            "encrypted_session_key": self.encrypted_session_key,
            "revoked": self.revoked,
            "created_at": self.created_at.isoformat(),
        }


# Back-populates fields
RoleDbModel.users = relationship(
    "UsersDbModel", order_by=UsersDbModel.id, back_populates="role"
)
LoginHistoryDbModel.user = relationship(
    "UsersDbModel", back_populates="login_histories"
)
UsersDbModel.refresh_tokens = relationship(
    "RefreshTokenDbModel",
    order_by=RefreshTokenDbModel.created_at,
    back_populates="user",
)
UsersDbModel.encryption_keys = relationship(
    "EncryptionKeysModel",
    order_by=EncryptionKeysModel.created_at,
    back_populates="user",
)

# Indexes
Index("idx_email", UsersDbModel.email)
Index("idx_login", UsersDbModel.login)


def combined_metadata():
    """
    Объединяет несколько объектов MetaData в один.
    """
    result = MetaData()
    metadatas = [
        UsersDbModel.metadata, 
        RoleDbModel.metadata, 
        LoginHistoryDbModel.metadata]
    for metadata in metadatas:
        for table in metadata.tables.values():
            table.tometadata(result)
    return result

