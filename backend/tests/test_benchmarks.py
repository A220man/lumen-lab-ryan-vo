"""Tests for benchmarks API."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.services.database import init_db


@pytest_asyncio.fixture(scope="module")
async def app():
    """Create app and initialize database."""
    app = create_app()
    await init_db()
    return app


@pytest_asyncio.fixture
async def client(app) -> AsyncClient:
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_benchmarks(client: AsyncClient):
    """Test list benchmarks endpoint."""
    response = await client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_create_benchmark(client: AsyncClient):
    """Test create benchmark endpoint."""
    response = await client.post("/api/v1/benchmarks", json={
        "name": "Test Benchmark",
        "driver": "lume"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Benchmark"
    assert data["driver"] == "lume"
    assert data["status"] == "pending"
    assert "id" in data
    return data["id"]


@pytest.mark.asyncio
async def test_get_benchmark(client: AsyncClient):
    """Test get benchmark endpoint."""
    # Create a benchmark first
    create_response = await client.post("/api/v1/benchmarks", json={
        "name": "Get Test Benchmark",
        "driver": "qemu"
    })
    assert create_response.status_code == 201
    benchmark_id = create_response.json()["id"]

    # Get the benchmark
    response = await client.get(f"/api/v1/benchmarks/{benchmark_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == benchmark_id
    assert data["name"] == "Get Test Benchmark"
    assert data["driver"] == "qemu"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_benchmark_not_found(client: AsyncClient):
    """Test get benchmark returns 404 for non-existent ID."""
    response = await client.get("/api/v1/benchmarks/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_run_benchmark(client: AsyncClient):
    """Test run benchmark endpoint."""
    # Create a benchmark first
    create_response = await client.post("/api/v1/benchmarks", json={
        "name": "Run Test Benchmark",
        "driver": "firecracker"
    })
    assert create_response.status_code == 201
    benchmark_id = create_response.json()["id"]

    # Run the benchmark
    response = await client.post(f"/api/v1/benchmarks/{benchmark_id}/run")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == benchmark_id
    assert data["status"] == "completed"
    assert data["iterations"] > 0
    assert data["avg_latency_ms"] is not None
    assert data["min_latency_ms"] is not None
    assert data["max_latency_ms"] is not None


@pytest.mark.asyncio
async def test_run_benchmark_not_found(client: AsyncClient):
    """Test run benchmark returns 400 for non-existent ID."""
    response = await client.post("/api/v1/benchmarks/99999/run")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_cancel_benchmark(client: AsyncClient):
    """Test cancel benchmark endpoint."""
    # Create a benchmark first
    create_response = await client.post("/api/v1/benchmarks", json={
        "name": "Cancel Test Benchmark",
        "driver": "docker"
    })
    assert create_response.status_code == 201
    benchmark_id = create_response.json()["id"]

    # Cancel the benchmark (it's in pending state, so should work)
    response = await client.post(f"/api/v1/benchmarks/{benchmark_id}/cancel")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == benchmark_id
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_benchmark_not_found(client: AsyncClient):
    """Test cancel benchmark returns 400 for non-existent ID."""
    response = await client.post("/api/v1/benchmarks/99999/cancel")
    assert response.status_code == 400

