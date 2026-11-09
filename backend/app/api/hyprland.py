"""Hyprland API for hyprland-isolated-input feature."""

from datetime import datetime, UTC
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import get_db
from app.services.hyprland import HyprlandService
from app.models.hyprland import (
    HyprlandSeat,
    HyprlandSeatStatus,
    HyprlandCapability,
    HyprlandOperatorRole,
    HyprlandCapabilityNegotiation,
    HyprlandAuthorizationRequest,
)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class HyprlandSeatCreateRequest(BaseModel):
    """Request to create a new Hyprland synthetic seat."""
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable seat name")
    seat_name: str = Field(..., min_length=1, max_length=64, description="Hyprland seat identifier (e.g., seat1)")
    operator_id: str = Field(..., min_length=1, max_length=255, description="Operator identifier")
    capabilities: List[HyprlandCapability] = Field(default_factory=list, description="Supported capabilities")
    operator_role: HyprlandOperatorRole = Field(default=HyprlandOperatorRole.OPERATOR, description="Operator role")
    udev_rules: Optional[str] = Field(None, description="Custom udev rules for device assignment")
    max_session_duration_minutes: int = Field(default=60, ge=1, le=1440, description="Max session duration in minutes")
    idle_timeout_minutes: int = Field(default=10, ge=1, le=1440, description="Idle timeout in minutes")
    labels: dict = Field(default_factory=dict, description="Metadata labels")
    description: Optional[str] = Field(None, description="Seat description")


class HyprlandSeatUpdateRequest(BaseModel):
    """Request to update a Hyprland seat."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    capabilities: Optional[List[HyprlandCapability]] = None
    operator_role: Optional[HyprlandOperatorRole] = None
    udev_rules: Optional[str] = None
    max_session_duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    idle_timeout_minutes: Optional[int] = Field(None, ge=1, le=1440)
    labels: Optional[dict] = None
    description: Optional[str] = None


class HyprlandSeatResponse(BaseModel):
    """Hyprland seat response."""
    id: int
    name: str
    seat_name: str
    status: HyprlandSeatStatus
    capabilities: List[str]
    operator_id: str
    operator_role: HyprlandOperatorRole
    udev_rules: Optional[str]
    max_session_duration_minutes: int
    idle_timeout_minutes: int
    labels: dict
    description: Optional[str]
    authorized_by: Optional[str]
    authorized_at: Optional[datetime]
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HyprlandSeatListResponse(BaseModel):
    """Paginated seat list response."""
    items: List[HyprlandSeatResponse]
    total: int
    page: int
    page_size: int


class HyprlandCapabilityNegotiationRequest(BaseModel):
    """Request to negotiate capabilities."""
    requested_capabilities: List[HyprlandCapability] = Field(..., min_length=1)


class HyprlandCapabilityNegotiationResponse(BaseModel):
    """Capability negotiation response."""
    id: int
    seat_id: int
    requested_capabilities: List[str]
    granted_capabilities: List[str]
    status: str
    negotiated_by: Optional[str]
    protocol_version: str
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HyprlandCapabilityNegotiationListResponse(BaseModel):
    """Paginated capability negotiation list response."""
    items: List[HyprlandCapabilityNegotiationResponse]
    total: int
    page: int
    page_size: int


class HyprlandAuthorizationRequestCreateRequest(BaseModel):
    """Request to create an authorization request."""
    operator_id: str = Field(..., min_length=1, max_length=255)
    seat_name: str = Field(..., min_length=1, max_length=64)
    requested_role: HyprlandOperatorRole = Field(default=HyprlandOperatorRole.OPERATOR)
    requested_capabilities: List[HyprlandCapability] = Field(default_factory=list)
    justification: Optional[str] = None


class HyprlandAuthorizationRequestResponse(BaseModel):
    """Authorization request response."""
    id: int
    operator_id: str
    seat_name: str
    requested_role: HyprlandOperatorRole
    requested_capabilities: List[str]
    justification: Optional[str]
    status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    denied_reason: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HyprlandAuthorizationRequestListResponse(BaseModel):
    """Paginated authorization request list response."""
    items: List[HyprlandAuthorizationRequestResponse]
    total: int
    page: int
    page_size: int


class HyprlandAuthorizationApproveRequest(BaseModel):
    """Request to approve an authorization request."""
    pass  # Just needs the path parameter


class HyprlandAuthorizationDenyRequest(BaseModel):
    """Request to deny an authorization request."""
    reason: str = Field(..., min_length=1)


class HyprlandConfigResponse(BaseModel):
    """Hyprland configuration response (for synthetic seat setup)."""
    seat_name: str
    udev_rules: Optional[str]
    capabilities: List[str]
    protocol_version: str = "1.0"


# =============================================================================
# Seat Endpoints
# =============================================================================

@router.get("/hyprland/seats", response_model=HyprlandSeatListResponse, tags=["hyprland"])
async def list_seats(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[HyprlandSeatStatus] = None,
    operator_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List synthetic seats with pagination and filtering."""
    service = HyprlandService(db)
    items, total = await service.list_seats(page=page, page_size=page_size, status=status, operator_id=operator_id)
    return HyprlandSeatListResponse(
        items=[HyprlandSeatResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/hyprland/seats", response_model=HyprlandSeatResponse, status_code=status.HTTP_201_CREATED, tags=["hyprland"])
async def create_seat(
    request: HyprlandSeatCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new synthetic seat."""
    service = HyprlandService(db)
    try:
        seat = await service.create_seat(
            name=request.name,
            seat_name=request.seat_name,
            operator_id=request.operator_id,
            capabilities=request.capabilities,
            operator_role=request.operator_role,
            udev_rules=request.udev_rules,
            max_session_duration_minutes=request.max_session_duration_minutes,
            idle_timeout_minutes=request.idle_timeout_minutes,
            labels=request.labels,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return HyprlandSeatResponse.model_validate(seat)


@router.get("/hyprland/seats/{seat_id}", response_model=HyprlandSeatResponse, tags=["hyprland"])
async def get_seat(
    seat_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a synthetic seat by ID."""
    service = HyprlandService(db)
    seat = await service.get_seat(seat_id)
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")
    return HyprlandSeatResponse.model_validate(seat)


@router.patch("/hyprland/seats/{seat_id}", response_model=HyprlandSeatResponse, tags=["hyprland"])
async def update_seat(
    seat_id: int,
    request: HyprlandSeatUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a synthetic seat."""
    service = HyprlandService(db)
    try:
        seat = await service.update_seat(
            seat_id=seat_id,
            name=request.name,
            capabilities=request.capabilities,
            operator_role=request.operator_role,
            udev_rules=request.udev_rules,
            max_session_duration_minutes=request.max_session_duration_minutes,
            idle_timeout_minutes=request.idle_timeout_minutes,
            labels=request.labels,
            description=request.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    await db.commit()
    return HyprlandSeatResponse.model_validate(seat)


@router.post("/hyprland/seats/{seat_id}/authorize", response_model=HyprlandSeatResponse, tags=["hyprland"])
async def authorize_seat(
    seat_id: int,
    authorized_by: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Authorize a pending seat (admin action)."""
    service = HyprlandService(db)
    try:
        seat = await service.authorize_seat(seat_id, authorized_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    await db.commit()
    return HyprlandSeatResponse.model_validate(seat)


@router.post("/hyprland/seats/{seat_id}/revoke", response_model=HyprlandSeatResponse, tags=["hyprland"])
async def revoke_seat(
    seat_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Revoke an active seat."""
    service = HyprlandService(db)
    try:
        seat = await service.revoke_seat(seat_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    await db.commit()
    return HyprlandSeatResponse.model_validate(seat)


@router.delete("/hyprland/seats/{seat_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["hyprland"])
async def delete_seat(
    seat_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a synthetic seat."""
    service = HyprlandService(db)
    success = await service.delete_seat(seat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Seat not found")
    await db.commit()


@router.get("/hyprland/seats/{seat_id}/config", response_model=HyprlandConfigResponse, tags=["hyprland"])
async def get_seat_config(
    seat_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get Hyprland configuration for a seat (for synthetic seat setup)."""
    service = HyprlandService(db)
    seat = await service.get_seat(seat_id)
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    if seat.status != HyprlandSeatStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Seat must be active to get config")

    return HyprlandConfigResponse(
        seat_name=seat.seat_name,
        udev_rules=seat.udev_rules,
        capabilities=seat.capabilities,
    )


# =============================================================================
# Capability Negotiation Endpoints
# =============================================================================

@router.post("/hyprland/seats/{seat_id}/negotiate", response_model=HyprlandCapabilityNegotiationResponse, tags=["hyprland"])
async def negotiate_capabilities(
    seat_id: int,
    request: HyprlandCapabilityNegotiationRequest,
    negotiated_by: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Negotiate capabilities for a seat."""
    service = HyprlandService(db)
    try:
        negotiation = await service.negotiate_capabilities(
            seat_id=seat_id,
            requested_capabilities=request.requested_capabilities,
            negotiated_by=negotiated_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return HyprlandCapabilityNegotiationResponse.model_validate(negotiation)


@router.get("/hyprland/seats/{seat_id}/negotiations", response_model=HyprlandCapabilityNegotiationListResponse, tags=["hyprland"])
async def list_negotiations(
    seat_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List capability negotiations for a seat."""
    service = HyprlandService(db)
    # Verify seat exists
    seat = await service.get_seat(seat_id)
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    items, total = await service.list_capability_negotiations(seat_id=seat_id, page=page, page_size=page_size)
    return HyprlandCapabilityNegotiationListResponse(
        items=[HyprlandCapabilityNegotiationResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# =============================================================================
# Authorization Request Endpoints
# =============================================================================

@router.post("/hyprland/authorize", response_model=HyprlandAuthorizationRequestResponse, status_code=status.HTTP_201_CREATED, tags=["hyprland"])
async def create_authorization_request(
    request: HyprlandAuthorizationRequestCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create an authorization request for a seat."""
    service = HyprlandService(db)
    try:
        auth_request = await service.create_authorization_request(
            operator_id=request.operator_id,
            seat_name=request.seat_name,
            requested_role=request.requested_role,
            requested_capabilities=request.requested_capabilities,
            justification=request.justification,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return HyprlandAuthorizationRequestResponse.model_validate(auth_request)


@router.get("/hyprland/authorize/{request_id}", response_model=HyprlandAuthorizationRequestResponse, tags=["hyprland"])
async def get_authorization_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an authorization request by ID."""
    service = HyprlandService(db)
    auth_request = await service.get_authorization_request(request_id)
    if not auth_request:
        raise HTTPException(status_code=404, detail="Authorization request not found")
    return HyprlandAuthorizationRequestResponse.model_validate(auth_request)


@router.post("/hyprland/authorize/{request_id}/approve", response_model=HyprlandAuthorizationRequestResponse, tags=["hyprland"])
async def approve_authorization_request(
    request_id: int,
    approved_by: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Approve an authorization request."""
    service = HyprlandService(db)
    try:
        auth_request = await service.approve_authorization_request(request_id, approved_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not auth_request:
        raise HTTPException(status_code=404, detail="Authorization request not found")

    await db.commit()
    return HyprlandAuthorizationRequestResponse.model_validate(auth_request)


@router.post("/hyprland/authorize/{request_id}/deny", response_model=HyprlandAuthorizationRequestResponse, tags=["hyprland"])
async def deny_authorization_request(
    request_id: int,
    request: HyprlandAuthorizationDenyRequest,
    denied_by: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Deny an authorization request."""
    service = HyprlandService(db)
    try:
        auth_request = await service.deny_authorization_request(request_id, denied_by, request.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not auth_request:
        raise HTTPException(status_code=404, detail="Authorization request not found")

    await db.commit()
    return HyprlandAuthorizationRequestResponse.model_validate(auth_request)


@router.get("/hyprland/authorize", response_model=HyprlandAuthorizationRequestListResponse, tags=["hyprland"])
async def list_authorization_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    operator_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List authorization requests."""
    service = HyprlandService(db)
    items, total = await service.list_authorization_requests(
        page=page, page_size=page_size, status=status, operator_id=operator_id
    )
    return HyprlandAuthorizationRequestListResponse(
        items=[HyprlandAuthorizationRequestResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
