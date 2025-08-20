import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import get_settings
from src.main import create_app

settings = get_settings()
pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    return "asyncio", {"use_uvloop": True}


@pytest.fixture(scope="session")
def app():
    """Создаем FastAPI app для тестов"""
    yield create_app()


@pytest.fixture(scope="session")
async def client_session(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=f"http://localhost{settings.root_path}{settings.api_prefix}",
    ) as ac:
        yield ac


@pytest.fixture
async def client(client_session):
    """Чистый HTTP-клиент для каждого теста, на основе session-клиента"""
    client_session.cookies.clear()
    client_session.headers.clear()
    return client_session
