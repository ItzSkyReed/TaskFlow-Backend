import io
import os
import uuid


async def get_random_symbols(amount: int = 16) -> str:
    return uuid.uuid4().hex[:amount]


async def get_random_bytes(size: int) -> io.BytesIO:
    data = os.urandom(size)
    return io.BytesIO(data)
