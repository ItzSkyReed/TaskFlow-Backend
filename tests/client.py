import pytest_asyncio

from httpx import AsyncClient, ASGITransport
from src.config import get_settings
from src.main import app

settings = get_settings()

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=f"http://localhost{settings.root_path}{settings.api_prefix}"
    ) as ac:
        yield ac
