"""Tests for auth API placeholder."""

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
async def test_login_endpoint(client: AsyncClient):
    """Test login endpoint returns 501."""
    response = await client.get("/api/v1/auth/login")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_callback_endpoint(client: AsyncClient):
    """Test callback endpoint returns 501."""
    response = await client.get("/api/v1/auth/callback")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient):
    """Test logout endpoint returns 501."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 501