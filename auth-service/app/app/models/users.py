from datetime import datetime
import uuid
from sqlalchemy import (
    Column,
    DateTime,
    String,
    ForeignKey,
    Index,
    LargeBinary,
    Text,
    Boolean,
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


class UsersDbModel(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    login = Column(String(255), nullable=False, unique=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    # encrypted_session_key = Column(LargeBinary)
    # public_key = Column(LargeBinary) # for test only
    # private_key = Column(LargeBinary) # for test only
    created_at = Column(DateTime, default=datetime.utcnow)
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=True
    )
    role = relationship("RoleDbModel", back_populates="users")
    login_histories = relationship("LoginHistoryDbModel", back_populates="user")


class LoginHistoryDbModel(Base):
    __tablename__ = "login_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ip = Column(String(255), nullable=False)
    user_agent = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("UsersDbModel", back_populates="login_histories")


class RefreshTokenDbModel(Base):
    __tablename__ = "refresh_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(Text, nullable=False, unique=True)  # Сам refresh токен
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(
        DateTime, nullable=False
    )  # Время истечения срока действия токена
    created_at = Column(DateTime, default=datetime.utcnow)  # Время создания токена
    revoked = Column(Boolean, default=False)  # Статус отзыва токена
    user = relationship("UsersDbModel", back_populates="refresh_tokens")


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
