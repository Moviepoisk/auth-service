from abc import ABC, abstractmethod
from typing import Optional
from redis.asyncio import Redis
import urllib
from functools import wraps
from typing import Callable
import json

class CacheManager(ABC):
    def __init__(self, default_expiry: int = 300):  # Default expiry 5 minutes
        self.default_expiry = default_expiry

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    async def set(self, key: str, value: str, expiry: Optional[int] = None) -> None:
        pass

    def generate_cache_key(self, *args) -> str:
        encoded_args = [urllib.parse.quote_plus(str(arg)) for arg in args]
        return ":".join(encoded_args)

class RedisCacheManager(CacheManager):
    def __init__(self, redis: Redis, default_expiry: int = 300):
        super().__init__(default_expiry)
        self.redis = redis

    async def get(self, key: str) -> Optional[str]:
        return await self.redis.get(key)

    async def set(self, key: str, value: str, expiry: Optional[int] = None) -> None:
        expiry = expiry if expiry is not None else self.default_expiry
        await self.redis.set(key, value, ex=expiry)

