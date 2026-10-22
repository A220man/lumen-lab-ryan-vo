"""Tests for hyprland API placeholder."""

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
async def test_get_hyprland_config(client: AsyncClient):
    """Test get hyprland config endpoint."""
    response = await client.get("/api/v1/hyprland/config")
    assert response.status_code == 501


@pytest.mark.asyncio
async def test_authorize_hyprland(client: AsyncClient):
    """Test authorize hyprland endpoint."""
    response = await client.post("/api/v1/hyprland/authorize", json={})
    assert response.status_code == 501