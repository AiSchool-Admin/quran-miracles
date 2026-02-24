"""Basic API tests."""

import importlib.util

import pytest

_has_fastapi = importlib.util.find_spec("fastapi") is not None
_has_httpx = importlib.util.find_spec("httpx") is not None

pytestmark = pytest.mark.skipif(
    not (_has_fastapi and _has_httpx),
    reason="fastapi or httpx not installed",
)


@pytest.fixture
async def client():
    from httpx import ASGITransport, AsyncClient

    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_list_surahs(client):
    response = await client.get("/api/quran/surahs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_discoveries(client):
    response = await client.get("/api/discovery/discoveries")
    assert response.status_code == 200
