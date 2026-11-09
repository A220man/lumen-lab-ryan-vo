"""Tests for hyprland-isolated-input feature."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import create_app
from app.services.database import get_db, init_db, close_db, reset_db
from app.models.hyprland import (
    HyprlandSeat,
    HyprlandSeatStatus,
    HyprlandCapability,
    HyprlandOperatorRole,
    HyprlandCapabilityNegotiation,
    HyprlandAuthorizationRequest,
)

@pytest_asyncio.fixture(scope="module")
async def app():
    """Create app and initialize database."""
    app = create_app()
    await reset_db()
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


# =============================================================================
# Seat Tests
# =============================================================================

@pytest.mark.asyncio
async def test_create_seat(client: AsyncClient):
    """Test creating a synthetic seat."""
    response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Test Seat",
        "seat_name": "seat1",
        "operator_id": "operator-123",
        "capabilities": ["input.mouse", "input.keyboard"],
        "operator_role": "operator",
        "max_session_duration_minutes": 60,
        "idle_timeout_minutes": 10,
        "labels": {"env": "test"},
        "description": "Test seat for isolated input"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Seat"
    assert data["seat_name"] == "seat1"
    assert data["operator_id"] == "operator-123"
    assert data["status"] == "pending"
    assert data["capabilities"] == ["input.mouse", "input.keyboard"]
    assert data["operator_role"] == "operator"
    assert data["labels"] == {"env": "test"}
    assert data["description"] == "Test seat for isolated input"
    assert data["id"] is not None
    return data["id"]


@pytest.mark.asyncio
async def test_create_seat_duplicate_name_fails(client: AsyncClient):
    """Test creating seat with duplicate name fails."""
    await client.post("/api/v1/hyprland/seats", json={
        "name": "Duplicate Seat",
        "seat_name": "seat2",
        "operator_id": "operator-123",
        "capabilities": ["input.mouse"],
    })
    response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Duplicate Seat",
        "seat_name": "seat3",
        "operator_id": "operator-123",
        "capabilities": ["input.mouse"],
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_seat_duplicate_seat_name_fails(client: AsyncClient):
    """Test creating seat with duplicate seat_name fails."""
    await client.post("/api/v1/hyprland/seats", json={
        "name": "Seat A",
        "seat_name": "duplicate-seat",
        "operator_id": "operator-123",
        "capabilities": ["input.mouse"],
    })
    response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Seat B",
        "seat_name": "duplicate-seat",
        "operator_id": "operator-123",
        "capabilities": ["input.keyboard"],
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_seats(client: AsyncClient):
    """Test listing seats."""
    response = await client.get("/api/v1/hyprland/seats")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_seats_with_filters(client: AsyncClient):
    """Test listing seats with filters."""
    # Create seats with different statuses and operators
    await client.post("/api/v1/hyprland/seats", json={
        "name": "Seat Filter Test 1",
        "seat_name": "filter-seat-1",
        "operator_id": "operator-filter-1",
        "capabilities": ["input.mouse"],
    })
    await client.post("/api/v1/hyprland/seats", json={
        "name": "Seat Filter Test 2",
        "seat_name": "filter-seat-2",
        "operator_id": "operator-filter-2",
        "capabilities": ["input.keyboard"],
    })

    # Filter by operator_id
    response = await client.get("/api/v1/hyprland/seats?operator_id=operator-filter-1")
    assert response.status_code == 200
    data = response.json()
    assert all(item["operator_id"] == "operator-filter-1" for item in data["items"])

    # Filter by status
    response = await client.get("/api/v1/hyprland/seats?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == "pending" for item in data["items"])


@pytest.mark.asyncio
async def test_get_seat(client: AsyncClient):
    """Test getting a seat by ID."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Get Seat Test",
        "seat_name": "get-seat-test",
        "operator_id": "operator-get",
        "capabilities": ["input.mouse", "input.keyboard"],
    })
    seat_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/hyprland/seats/{seat_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == seat_id
    assert data["name"] == "Get Seat Test"
    assert data["seat_name"] == "get-seat-test"


@pytest.mark.asyncio
async def test_get_seat_not_found(client: AsyncClient):
    """Test getting non-existent seat returns 404."""
    response = await client.get("/api/v1/hyprland/seats/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_seat(client: AsyncClient):
    """Test updating a seat."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Update Seat Test",
        "seat_name": "update-seat-test",
        "operator_id": "operator-update",
        "capabilities": ["input.mouse"],
    })
    seat_id = create_response.json()["id"]

    response = await client.patch(f"/api/v1/hyprland/seats/{seat_id}", json={
        "name": "Updated Seat Name",
        "capabilities": ["input.mouse", "input.keyboard", "input.touch"],
        "max_session_duration_minutes": 120,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Seat Name"
    assert data["capabilities"] == ["input.mouse", "input.keyboard", "input.touch"]
    assert data["max_session_duration_minutes"] == 120


@pytest.mark.asyncio
async def test_update_seat_not_found(client: AsyncClient):
    """Test updating non-existent seat returns 404."""
    response = await client.patch("/api/v1/hyprland/seats/99999", json={"name": "New Name"})
    assert response.status_code == 404


# =============================================================================
# Authorization Tests
# =============================================================================

@pytest.mark.asyncio
async def test_authorize_seat(client: AsyncClient):
    """Test authorizing a pending seat."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Authorize Seat Test",
        "seat_name": "authorize-seat-test",
        "operator_id": "operator-auth",
        "capabilities": ["input.mouse"],
    })
    seat_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/hyprland/seats/{seat_id}/authorize?authorized_by=admin-123")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["authorized_by"] == "admin-123"
    assert data["authorized_at"] is not None


@pytest.mark.asyncio
async def test_authorize_seat_not_pending_fails(client: AsyncClient):
    """Test authorizing non-pending seat fails."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Auth Fail Test",
        "seat_name": "auth-fail-test",
        "operator_id": "operator-auth-fail",
        "capabilities": ["input.mouse"],
    })
    seat_id = create_response.json()["id"]

    # First authorize it
    await client.post(f"/api/v1/hyprland/seats/{seat_id}/authorize?authorized_by=admin-123")

    # Try to authorize again
    response = await client.post(f"/api/v1/hyprland/seats/{seat_id}/authorize?authorized_by=admin-456")
    assert response.status_code == 400
    assert "not in pending status" in response.json()["detail"]


@pytest.mark.asyncio
async def test_revoke_seat(client: AsyncClient):
    """Test revoking an active seat."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Revoke Seat Test",
        "seat_name": "revoke-seat-test",
        "operator_id": "operator-revoke",
        "capabilities": ["input.mouse"],
    })
    seat_id = create_response.json()["id"]

    # Authorize first
    await client.post(f"/api/v1/hyprland/seats/{seat_id}/authorize?authorized_by=admin-123")

    # Then revoke
    response = await client.post(f"/api/v1/hyprland/seats/{seat_id}/revoke")
    assert response.status_code == 200
    data = response.json()
@pytest.mark.asyncio
async def test_revoke_seat_invalid_status_fails(client: AsyncClient):
    """Test revoking seat in invalid status fails."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Revoke Fail Test",
        "seat_name": "revoke-fail-test",
        "operator_id": "operator-revoke-fail",
        "capabilities": ["input.mouse"],
    })
    seat_id = create_response.json()["id"]

    # Authorize first
    await client.post(f"/api/v1/hyprland/seats/{seat_id}/authorize?authorized_by=admin-123")

    # Revoke it
    await client.post(f"/api/v1/hyprland/seats/{seat_id}/revoke")

    # Try to revoke again (already revoked)
    response = await client.post(f"/api/v1/hyprland/seats/{seat_id}/revoke")
    assert response.status_code == 400
    assert "cannot be revoked" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_seat(client: AsyncClient):
    """Test deleting a seat."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Delete Seat Test",
        "seat_name": "delete-seat-test",
        "operator_id": "operator-delete",
        "capabilities": ["input.mouse"],
    })
    seat_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/hyprland/seats/{seat_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/v1/hyprland/seats/{seat_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_seat_config(client: AsyncClient):
    """Test getting seat configuration for Hyprland setup."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Config Seat Test",
        "seat_name": "config-seat-test",
        "operator_id": "operator-config",
        "capabilities": ["input.mouse", "input.keyboard"],
        "udev_rules": 'SUBSYSTEM=="input", TAG+="uaccess"',
    })
    seat_id = create_response.json()["id"]

    # Authorize first
    await client.post(f"/api/v1/hyprland/seats/{seat_id}/authorize?authorized_by=admin-123")

    # Get config
    response = await client.get(f"/api/v1/hyprland/seats/{seat_id}/config")
    assert response.status_code == 200
    data = response.json()
    assert data["seat_name"] == "config-seat-test"
    assert data["capabilities"] == ["input.mouse", "input.keyboard"]
    assert data["udev_rules"] == 'SUBSYSTEM=="input", TAG+="uaccess"'
    assert data["protocol_version"] == "1.0"


@pytest.mark.asyncio
async def test_get_seat_config_not_active_fails(client: AsyncClient):
    """Test getting config for non-active seat fails."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Config Fail Test",
        "seat_name": "config-fail-test",
        "operator_id": "operator-config-fail",
        "capabilities": ["input.mouse"],
    })
    seat_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/hyprland/seats/{seat_id}/config")
    assert response.status_code == 400
    assert "must be active" in response.json()["detail"]


# =============================================================================
# Capability Negotiation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_negotiate_capabilities(client: AsyncClient):
    """Test negotiating capabilities for a seat."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Negotiate Seat Test",
        "seat_name": "negotiate-seat-test",
        "operator_id": "operator-negotiate",
        "capabilities": ["input.mouse", "input.keyboard", "clipboard"],
    })
    seat_id = create_response.json()["id"]

    # Authorize first
    await client.post(f"/api/v1/hyprland/seats/{seat_id}/authorize?authorized_by=admin-123")

    # Negotiate capabilities
    response = await client.post(
        f"/api/v1/hyprland/seats/{seat_id}/negotiate?negotiated_by=admin-123",
        json={"requested_capabilities": ["input.mouse", "clipboard", "drag_drop"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["seat_id"] == seat_id
    assert set(data["requested_capabilities"]) == {"input.mouse", "clipboard", "drag_drop"}
    # Only input.mouse and clipboard are supported by the seat
    assert set(data["granted_capabilities"]) == {"input.mouse", "clipboard"}
    assert data["status"] == "granted"
    assert data["negotiated_by"] == "admin-123"


@pytest.mark.asyncio
async def test_negotiate_capabilities_not_active_fails(client: AsyncClient):
    """Test negotiating capabilities for non-active seat fails."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Negotiate Fail Test",
        "seat_name": "negotiate-fail-test",
        "operator_id": "operator-negotiate-fail",
        "capabilities": ["input.mouse"],
    })
    seat_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/hyprland/seats/{seat_id}/negotiate?negotiated_by=admin-123",
        json={"requested_capabilities": ["input.mouse"]}
    )
    assert response.status_code == 400
    assert "must be active" in response.json()["detail"]


@pytest.mark.asyncio
async def test_negotiate_capabilities_none_granted(client: AsyncClient):
    """Test negotiating capabilities where none are supported."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "Negotiate None Test",
        "seat_name": "negotiate-none-test",
        "operator_id": "operator-negotiate-none",
        "capabilities": ["input.mouse"],
    })
    seat_id = create_response.json()["id"]

    await client.post(f"/api/v1/hyprland/seats/{seat_id}/authorize?authorized_by=admin-123")

    response = await client.post(
        f"/api/v1/hyprland/seats/{seat_id}/negotiate?negotiated_by=admin-123",
        json={"requested_capabilities": ["output.display", "drag_drop"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["granted_capabilities"] == []
    assert data["status"] == "denied"


@pytest.mark.asyncio
async def test_list_negotiations(client: AsyncClient):
    """Test listing capability negotiations for a seat."""
    create_response = await client.post("/api/v1/hyprland/seats", json={
        "name": "List Negotiations Test",
        "seat_name": "list-negotiations-test",
        "operator_id": "operator-list-neg",
        "capabilities": ["input.mouse", "input.keyboard"],
    })
    seat_id = create_response.json()["id"]

    await client.post(f"/api/v1/hyprland/seats/{seat_id}/authorize?authorized_by=admin-123")

    # Create multiple negotiations
    await client.post(
        f"/api/v1/hyprland/seats/{seat_id}/negotiate?negotiated_by=admin-123",
        json={"requested_capabilities": ["input.mouse"]}
    )
    await client.post(
        f"/api/v1/hyprland/seats/{seat_id}/negotiate?negotiated_by=admin-456",
        json={"requested_capabilities": ["input.keyboard"]}
    )

    response = await client.get(f"/api/v1/hyprland/seats/{seat_id}/negotiations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


# =============================================================================
# Authorization Request Tests
# =============================================================================

@pytest.mark.asyncio
async def test_create_authorization_request(client: AsyncClient):
    """Test creating an authorization request."""
    # First create a seat
    await client.post("/api/v1/hyprland/seats", json={
        "name": "Auth Request Seat",
        "seat_name": "auth-request-seat",
        "operator_id": "operator-auth-req",
        "capabilities": ["input.mouse", "input.keyboard"],
    })

    response = await client.post("/api/v1/hyprland/authorize", json={
        "operator_id": "operator-456",
        "seat_name": "auth-request-seat",
        "requested_role": "operator",
        "requested_capabilities": ["input.mouse"],
        "justification": "Need access for testing"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["operator_id"] == "operator-456"
    assert data["seat_name"] == "auth-request-seat"
    assert data["requested_role"] == "operator"
    assert data["requested_capabilities"] == ["input.mouse"]
    assert data["justification"] == "Need access for testing"
    assert data["status"] == "pending"
    return data["id"]


@pytest.mark.asyncio
async def test_create_authorization_request_seat_not_found(client: AsyncClient):
    """Test creating auth request for non-existent seat fails."""
    response = await client.post("/api/v1/hyprland/authorize", json={
        "operator_id": "operator-456",
        "seat_name": "non-existent-seat",
        "requested_role": "operator",
        "requested_capabilities": ["input.mouse"],
    })
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_authorization_request(client: AsyncClient):
    """Test getting an authorization request by ID."""
    create_response = await client.post("/api/v1/hyprland/authorize", json={
        "operator_id": "operator-get-auth",
        "seat_name": "auth-request-seat",  # Already exists from previous test
        "requested_role": "operator",
        "requested_capabilities": ["input.keyboard"],
    })
    request_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/hyprland/authorize/{request_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == request_id
    assert data["operator_id"] == "operator-get-auth"


@pytest.mark.asyncio
async def test_approve_authorization_request(client: AsyncClient):
    """Test approving an authorization request."""
    create_response = await client.post("/api/v1/hyprland/authorize", json={
        "operator_id": "operator-approve",
        "seat_name": "auth-request-seat",
        "requested_role": "operator",
        "requested_capabilities": ["input.mouse"],
    })
    request_id = create_response.json()["id"]

    response = await client.post(f"/api/v1/hyprland/authorize/{request_id}/approve?approved_by=admin-123")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["approved_by"] == "admin-123"
    assert data["approved_at"] is not None


@pytest.mark.asyncio
async def test_deny_authorization_request(client: AsyncClient):
    """Test denying an authorization request."""
    create_response = await client.post("/api/v1/hyprland/authorize", json={
        "operator_id": "operator-deny",
        "seat_name": "auth-request-seat",
        "requested_role": "operator",
        "requested_capabilities": ["input.mouse"],
    })
    request_id = create_response.json()["id"]

    response = await client.post(
        f"/api/v1/hyprland/authorize/{request_id}/deny?denied_by=admin-123",
        json={"reason": "Insufficient privileges"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "denied"
    assert data["approved_by"] == "admin-123"
    assert data["denied_reason"] == "Insufficient privileges"
    assert data["approved_at"] is not None


@pytest.mark.asyncio
async def test_list_authorization_requests(client: AsyncClient):
    """Test listing authorization requests."""
    response = await client.get("/api/v1/hyprland/authorize")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)

    # Filter by status
    response = await client.get("/api/v1/hyprland/authorize?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == "pending" for item in data["items"])

    # Filter by operator_id
    response = await client.get("/api/v1/hyprland/authorize?operator_id=operator-approve")
    assert response.status_code == 200
    data = response.json()
    assert all(item["operator_id"] == "operator-approve" for item in data["items"])
