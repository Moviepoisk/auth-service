from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from jose import JWTError, jwt

from app.core.config import settings
from app.exceptions.exceptions import get_token_validation_exception
from app.schemas.auth import AccessTokenData, RefreshTokenData


class TokenStrategy(ABC):
    @abstractmethod
    def create_token(self, *, data: dict, expires_delta: timedelta) -> str:
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> AccessTokenData | RefreshTokenData:
        pass


class AccessTokenStrategy(TokenStrategy):
    async def create_token(self, *, data: dict, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        return encoded_jwt

    async def verify_token(self, token: str) -> AccessTokenData:
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            login: str = payload.get("sub")
            if not login:
                raise get_token_validation_exception()
            token_data = AccessTokenData(login=login)
        except JWTError:
            raise get_token_validation_exception()
        return token_data


class RefreshTokenStrategy(TokenStrategy):
    async def create_token(self, *, data: dict, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        return encoded_jwt

    async def verify_token(self, token: str) -> RefreshTokenData:
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            login: str = payload.get("sub")
            if not login:
                raise get_token_validation_exception()
            token_data = RefreshTokenData(login=login)
        except JWTError:
            raise get_token_validation_exception()
        return token_data
