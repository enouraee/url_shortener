import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz_returns_ok(client: AsyncClient):
    """Healthz should return 200."""
    response = await client.get("/healthz")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz_returns_ok_when_db_reachable(client: AsyncClient):
    """Readyz should return 200 when DB is up."""
    response = await client.get("/readyz")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
