import asyncio
from Crypto.Random import get_random_bytes

async def get_session_key_async():
    loop = asyncio.get_running_loop()
    session_key = await loop.run_in_executor(None, get_random_bytes, 16)
    return session_key