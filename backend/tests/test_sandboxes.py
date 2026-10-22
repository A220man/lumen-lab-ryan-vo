"""Tests for sandboxes API placeholder."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


@pytest.fixture
def client() -> AsyncClient:
    """Create test client."""
    app = create_app()
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_list_sandboxes(client: AsyncClient):
    """Test list sandboxes endpoint."""
    response = await client.get("/api/v1/sandboxes")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_create_sandbox_returns_not_implemented(client: AsyncClient):
    """Test create sandbox returns 501."""
    response = await client.post("/api/v1/sandboxes", json={})
    assert response.status_code == 501