"""Tests for sandboxes API."""

import pytest_asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.services.database import init_db, close_db, get_db
from app.models.sandbox import Sandbox, SandboxStatus, SandboxProvider, SandboxArchitecture
from sqlalchemy import select


@pytest_asyncio.fixture(scope="module")
async def app():
    """Create app and initialize database."""
    app = create_app()
    await init_db()
    yield app
    await close_db()


@pytest_asyncio.fixture
async def client(app) -> AsyncClient:
    """Create test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session(app):
    """Get database session for direct model access."""
    async for session in get_db():
        yield session


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
async def test_create_sandbox(client: AsyncClient):
    """Test create sandbox endpoint."""
    response = await client.post("/api/v1/sandboxes", json={
        "name": "test-sandbox",
        "provider": "docker",
        "image": "ghcr.io/test/image:latest",
        "architecture": "amd64",
        "cpu": 2,
        "memory_mb": 4096,
        "disk_gb": 20,
        "ports": [],
        "network_mode": "bridge",
        "labels": {},
        "auto_remove": True,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-sandbox"
    assert data["provider"] == "docker"
    assert data["architecture"] == "amd64"
    assert data["status"] == "creating"
    assert data["image"] == "ghcr.io/test/image:latest"
    assert data["cpu"] == 2
    assert data["memory_mb"] == 4096
    assert data["disk_gb"] == 20
    assert "id" in data
    return data["id"]


@pytest.mark.asyncio
async def test_get_sandbox(client: AsyncClient):
    """Test get sandbox endpoint."""
    # First create a sandbox
    create_response = await client.post("/api/v1/sandboxes", json={
        "name": "test-sandbox-get",
        "provider": "lume",
        "image": "ghcr.io/lume/lume:latest",
        "architecture": "arm64",
    })
    assert create_response.status_code == 201
    sandbox_id = create_response.json()["id"]

    # Now get it
    response = await client.get(f"/api/v1/sandboxes/{sandbox_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sandbox_id
    assert data["name"] == "test-sandbox-get"
    assert data["provider"] == "lume"
    assert data["architecture"] == "arm64"


@pytest.mark.asyncio
async def test_get_sandbox_not_found(client: AsyncClient):
    """Test get sandbox returns 404 for non-existent ID."""
    response = await client.get("/api/v1/sandboxes/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_sandbox(client: AsyncClient):
    """Test update sandbox endpoint."""
    create_response = await client.post("/api/v1/sandboxes", json={
        "name": "test-sandbox-update",
        "provider": "qemu",
        "image": "ghcr.io/test/qemu:latest",
    })
    assert create_response.status_code == 201
    sandbox_id = create_response.json()["id"]

    response = await client.patch(f"/api/v1/sandboxes/{sandbox_id}", json={
        "name": "updated-sandbox",
        "cpu": 4,
        "memory_mb": 8192,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-sandbox"
    assert data["cpu"] == 4
    assert data["memory_mb"] == 8192


@pytest.mark.asyncio
async def test_start_sandbox(client: AsyncClient):
    """Test start sandbox endpoint."""
    create_response = await client.post("/api/v1/sandboxes", json={
        "name": "test-sandbox-start",
        "provider": "firecracker",
        "image": "ghcr.io/test/firecracker:latest",
    })
    assert create_response.status_code == 201
    sandbox_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["container_id"] is not None
    assert data["ip_address"] is not None
    assert data["started_at"] is not None


@pytest.mark.asyncio
async def test_start_sandbox_invalid_status(client: AsyncClient):
    """Test start sandbox fails for already running sandbox."""
    create_response = await client.post("/api/v1/sandboxes", json={
        "name": "test-sandbox-start-invalid",
        "provider": "docker",
        "image": "ghcr.io/test/docker:latest",
    })
    assert create_response.status_code == 201
    sandbox_id = create_response.json()["id"]

    # Start once
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")
    # Try to start again
    response = await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_stop_sandbox(client: AsyncClient):
    """Test stop sandbox endpoint."""
    create_response = await client.post("/api/v1/sandboxes", json={
        "name": "test-sandbox-stop",
        "provider": "docker",
        "image": "ghcr.io/test/docker:latest",
    })
    assert create_response.status_code == 201
    sandbox_id = create_response.json()["id"]

    # Start first
    await client.post(f"/api/v1/sandboxes/{sandbox_id}/start")

    # Then stop
    response = await client.post(f"/api/v1/sandboxes/{sandbox_id}/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"
    assert data["stopped_at"] is not None


@pytest.mark.asyncio
async def test_stop_sandbox_invalid_status(client: AsyncClient):
    """Test stop sandbox fails for non-running sandbox."""
    create_response = await client.post("/api/v1/sandboxes", json={
        "name": "test-sandbox-stop-invalid",
        "provider": "docker",
        "image": "ghcr.io/test/docker:latest",
    })
    assert create_response.status_code == 201
    sandbox_id = create_response.json()["id"]

    # Try to stop without starting
    response = await client.post(f"/api/v1/sandboxes/{sandbox_id}/stop")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_sandbox(client: AsyncClient):
    """Test delete sandbox endpoint."""
    create_response = await client.post("/api/v1/sandboxes", json={
        "name": "test-sandbox-delete",
        "provider": "docker",
        "image": "ghcr.io/test/docker:latest",
    })
    assert create_response.status_code == 201
    sandbox_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/sandboxes/{sandbox_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/v1/sandboxes/{sandbox_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_sandbox_not_found(client: AsyncClient):
    """Test delete sandbox returns 404 for non-existent ID."""
    response = await client.delete("/api/v1/sandboxes/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_sandboxes_with_filters(client: AsyncClient):
    """Test list sandboxes with filtering."""
    # Create sandboxes with different providers
    await client.post("/api/v1/sandboxes", json={
        "name": "docker-sandbox-1",
        "provider": "docker",
        "image": "ghcr.io/test/docker:latest",
    })
    await client.post("/api/v1/sandboxes", json={
        "name": "docker-sandbox-2",
        "provider": "docker",
        "image": "ghcr.io/test/docker:latest",
    })
    await client.post("/api/v1/sandboxes", json={
        "name": "lume-sandbox",
        "provider": "lume",
        "image": "ghcr.io/lume/lume:latest",
    })

    # Filter by provider
    response = await client.get("/api/v1/sandboxes?provider=docker")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert all(item["provider"] == "docker" for item in data["items"])

    # Filter by architecture
    response = await client.get("/api/v1/sandboxes?architecture=amd64")
    assert response.status_code == 200
    data = response.json()
    assert all(item["architecture"] == "amd64" for item in data["items"])


@pytest.mark.asyncio
async def test_sandbox_ports(client: AsyncClient):
    """Test sandbox port mappings."""
    create_response = await client.post("/api/v1/sandboxes", json={
        "name": "test-sandbox-ports",
        "provider": "docker",
        "image": "ghcr.io/test/docker:latest",
        "ports": [
            {"host_port": 8080, "container_port": 80, "protocol": "tcp"},
            {"host_port": 8443, "container_port": 443, "protocol": "tcp"},
        ],
    })
    assert create_response.status_code == 201
    sandbox_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/sandboxes/{sandbox_id}/ports")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["host_port"] == 8080
    assert data[0]["container_port"] == 80
    assert data[1]["host_port"] == 8443
    assert data[1]["container_port"] == 443


@pytest.mark.asyncio
async def test_sandbox_with_arm64_architecture(client: AsyncClient):
    """Test creating sandbox with ARM64 architecture (issue #353)."""
    response = await client.post("/api/v1/sandboxes", json={
        "name": "arm64-sandbox",
        "provider": "lume",
        "image": "ghcr.io/lume/lume:arm64-latest",
        "architecture": "arm64",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["architecture"] == "arm64"
    assert data["provider"] == "lume"


@pytest.mark.asyncio
async def test_sandbox_with_ghcr_image(client: AsyncClient):
    """Test creating sandbox with GHCR image reference (issue #22)."""
    response = await client.post("/api/v1/sandboxes", json={
        "name": "ghcr-sandbox",
        "provider": "docker",
        "image": "ghcr.io/owner/repo:tag",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["image"] == "ghcr.io/owner/repo:tag"
