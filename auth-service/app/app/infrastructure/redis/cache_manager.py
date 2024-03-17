import orjson
from typing import Optional, Any
from redis.asyncio import Redis
import urllib
from abc import ABC, abstractmethod
import functools

CACHE_EXPIRE_IN_SECONDS = 300  # Пример значения, адаптируйте под свои нужды

class CacheManager(ABC):
    def __init__(self, default_expiry: int = CACHE_EXPIRE_IN_SECONDS):
        self.default_expiry = default_expiry

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, expiry: Optional[int] = None) -> None:
        pass

    def generate_cache_key(self, *args) -> str:
        return ":".join(map(str, args))

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

class RedisCacheManager(CacheManager):
    def __init__(self, redis: Redis, default_expiry: int = CACHE_EXPIRE_IN_SECONDS):
        super().__init__(default_expiry)
        self.redis = redis
    

    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        if data:
            return orjson.loads(data)
        return None

    async def set(self, key: str, value: Any, expiry: Optional[int] = None) -> None:
        try:
            serialized_value = orjson.dumps(value).decode('utf-8')
            expiry = expiry if expiry is not None else self.default_expiry
            await self.redis.set(key, serialized_value, ex=expiry)
        except Exception as e:
            print(f"Error serializing data to Redis: {e}")

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)
