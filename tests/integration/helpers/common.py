import uuid


async def get_random_symbols(amount: int = 16) -> str:
    return uuid.uuid4().hex[:amount]