import uuid

import pytest
from client import client
from src.auth import auth_router

@pytest.mark.asyncio
async def test_sign_up(client):
    unique = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Joe_Sardina{unique}",
        "login": f"Joe_Sardina{unique}",
        "email": f"johndoe{unique}@example.com",
        "password": "dM9O*KcgZ91w$WAfG1a$!G9V$5Lav65Zf"
    }

    response = await client.post(f"{auth_router.prefix}/sign_up", json=payload)

    assert response.status_code == 200
