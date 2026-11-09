"""Hyprland service for hyprland-isolated-input feature."""

import uuid
from datetime import datetime, UTC, timedelta
from typing import List, Optional, Tuple, Set

from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hyprland import (
    HyprlandSeat,
    HyprlandSeatStatus,
    HyprlandCapability,
    HyprlandOperatorRole,
    HyprlandCapabilityNegotiation,
    HyprlandAuthorizationRequest,
)
from app.core.config import get_settings


class HyprlandService:
    """Service for managing Hyprland isolated input configuration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def create_seat(
        self,
        name: str,
        seat_name: str,
        operator_id: str,
        capabilities: List[HyprlandCapability],
        operator_role: HyprlandOperatorRole = HyprlandOperatorRole.OPERATOR,
        udev_rules: Optional[str] = None,
        max_session_duration_minutes: int = 60,
        idle_timeout_minutes: int = 10,
        labels: Optional[dict] = None,
        description: Optional[str] = None,
    ) -> HyprlandSeat:
        """Create a new synthetic seat."""
        # Check seat_name uniqueness
        existing = await self.db.execute(
            select(HyprlandSeat).where(HyprlandSeat.seat_name == seat_name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Seat name '{seat_name}' already exists")

        # Check name uniqueness
        existing = await self.db.execute(
            select(HyprlandSeat).where(HyprlandSeat.name == name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Seat with name '{name}' already exists")

        expires_at = datetime.now(UTC) + timedelta(minutes=max_session_duration_minutes)

        seat = HyprlandSeat(
            name=name,
            seat_name=seat_name,
            operator_id=operator_id,
            operator_role=operator_role,
            capabilities=[c.value for c in capabilities],
            udev_rules=udev_rules,
            max_session_duration_minutes=max_session_duration_minutes,
            idle_timeout_minutes=idle_timeout_minutes,
            labels=labels or {},
            description=description,
            expires_at=expires_at,
            status=HyprlandSeatStatus.PENDING,
        )
        self.db.add(seat)
        await self.db.flush()
        return seat

    async def get_seat(self, seat_id: int) -> Optional[HyprlandSeat]:
        """Get a seat by ID."""
        result = await self.db.execute(select(HyprlandSeat).where(HyprlandSeat.id == seat_id))
        return result.scalar_one_or_none()

    async def get_seat_by_name(self, seat_name: str) -> Optional[HyprlandSeat]:
        """Get a seat by seat_name."""
        result = await self.db.execute(select(HyprlandSeat).where(HyprlandSeat.seat_name == seat_name))
        return result.scalar_one_or_none()

    async def list_seats(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[HyprlandSeatStatus] = None,
        operator_id: Optional[str] = None,
    ) -> Tuple[List[HyprlandSeat], int]:
        """List seats with pagination and filtering."""
        query = select(HyprlandSeat)
        count_query = select(func.count(HyprlandSeat.id))

        conditions = []
        if status:
            conditions.append(HyprlandSeat.status == status)
        if operator_id:
            conditions.append(HyprlandSeat.operator_id == operator_id)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.order_by(HyprlandSeat.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update_seat(
        self,
        seat_id: int,
        name: Optional[str] = None,
        capabilities: Optional[List[HyprlandCapability]] = None,
        operator_role: Optional[HyprlandOperatorRole] = None,
        udev_rules: Optional[str] = None,
        max_session_duration_minutes: Optional[int] = None,
        idle_timeout_minutes: Optional[int] = None,
        labels: Optional[dict] = None,
        description: Optional[str] = None,
    ) -> Optional[HyprlandSeat]:
        """Update a seat."""
        seat = await self.get_seat(seat_id)
        if not seat:
            return None

        if name is not None:
            existing = await self.db.execute(
                select(HyprlandSeat).where(
                    and_(HyprlandSeat.name == name, HyprlandSeat.id != seat_id)
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Seat with name '{name}' already exists")
            seat.name = name

        if capabilities is not None:
            seat.capabilities = [c.value for c in capabilities]

        if operator_role is not None:
            seat.operator_role = operator_role

        if udev_rules is not None:
            seat.udev_rules = udev_rules

        if max_session_duration_minutes is not None:
            seat.max_session_duration_minutes = max_session_duration_minutes
            seat.expires_at = datetime.now(UTC) + timedelta(minutes=max_session_duration_minutes)

        if idle_timeout_minutes is not None:
            seat.idle_timeout_minutes = idle_timeout_minutes

        if labels is not None:
            seat.labels = labels

        if description is not None:
            seat.description = description

        seat.updated_at = datetime.now(UTC)
        await self.db.flush()
        return seat

    async def authorize_seat(self, seat_id: int, authorized_by: str) -> Optional[HyprlandSeat]:
        """Authorize a pending seat (admin action)."""
        seat = await self.get_seat(seat_id)
        if not seat:
            return None

        if seat.status != HyprlandSeatStatus.PENDING:
            raise ValueError(f"Seat is not in pending status: {seat.status}")

        seat.status = HyprlandSeatStatus.ACTIVE
        seat.authorized_by = authorized_by
        seat.authorized_at = datetime.now(UTC)
        seat.updated_at = datetime.now(UTC)
        await self.db.flush()
        return seat

    async def revoke_seat(self, seat_id: int) -> Optional[HyprlandSeat]:
        """Revoke an active seat."""
        seat = await self.get_seat(seat_id)
        if not seat:
            return None

        if seat.status not in [HyprlandSeatStatus.ACTIVE, HyprlandSeatStatus.PENDING]:
            raise ValueError(f"Seat cannot be revoked from status: {seat.status}")

        seat.status = HyprlandSeatStatus.REVOKED
        seat.revoked_at = datetime.now(UTC)
        seat.updated_at = datetime.now(UTC)
        await self.db.flush()
        return seat

    async def delete_seat(self, seat_id: int) -> bool:
        """Delete a seat."""
        seat = await self.get_seat(seat_id)
        if not seat:
            return False

        await self.db.delete(seat)
        await self.db.flush()
        return True

    async def negotiate_capabilities(
        self,
        seat_id: int,
        requested_capabilities: List[HyprlandCapability],
        negotiated_by: str,
    ) -> HyprlandCapabilityNegotiation:
        """Negotiate capabilities for a seat."""
        seat = await self.get_seat(seat_id)
        if not seat:
            raise ValueError(f"Seat {seat_id} not found")

        # Check if seat is active
        if seat.status != HyprlandSeatStatus.ACTIVE:
            raise ValueError(f"Seat must be active for capability negotiation, current: {seat.status}")

        # Grant capabilities that the seat supports
        seat_capabilities = set(HyprlandCapability(c) for c in seat.capabilities)
        requested_set = set(requested_capabilities)
        granted = list(seat_capabilities & requested_set)
        denied = list(requested_set - seat_capabilities)

        negotiation = HyprlandCapabilityNegotiation(
            seat_id=seat_id,
            requested_capabilities=[c.value for c in requested_capabilities],
            granted_capabilities=[c.value for c in granted],
            status="granted" if granted else "denied",
            negotiated_by=negotiated_by,
            expires_at=datetime.now(UTC) + timedelta(minutes=seat.max_session_duration_minutes),
        )
        self.db.add(negotiation)
        await self.db.flush()
        return negotiation

    async def get_capability_negotiation(self, negotiation_id: int) -> Optional[HyprlandCapabilityNegotiation]:
        """Get a capability negotiation by ID."""
        result = await self.db.execute(
            select(HyprlandCapabilityNegotiation).where(HyprlandCapabilityNegotiation.id == negotiation_id)
        )
        return result.scalar_one_or_none()

    async def list_capability_negotiations(
        self,
        seat_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[HyprlandCapabilityNegotiation], int]:
        """List capability negotiations for a seat."""
        query = select(HyprlandCapabilityNegotiation).where(HyprlandCapabilityNegotiation.seat_id == seat_id)
        count_query = select(func.count(HyprlandCapabilityNegotiation.id)).where(
            HyprlandCapabilityNegotiation.seat_id == seat_id
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(HyprlandCapabilityNegotiation.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def create_authorization_request(
        self,
        operator_id: str,
        seat_name: str,
        requested_role: HyprlandOperatorRole,
        requested_capabilities: List[HyprlandCapability],
        justification: Optional[str] = None,
    ) -> HyprlandAuthorizationRequest:
        """Create an authorization request."""
        # Check if seat exists
        seat = await self.get_seat_by_name(seat_name)
        if not seat:
            raise ValueError(f"Seat '{seat_name}' not found")

        request = HyprlandAuthorizationRequest(
            operator_id=operator_id,
            seat_name=seat_name,
            requested_role=requested_role,
            requested_capabilities=[c.value for c in requested_capabilities],
            justification=justification,
            status="pending",
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        self.db.add(request)
        await self.db.flush()
        return request

    async def get_authorization_request(self, request_id: int) -> Optional[HyprlandAuthorizationRequest]:
        """Get an authorization request by ID."""
        result = await self.db.execute(
            select(HyprlandAuthorizationRequest).where(HyprlandAuthorizationRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def approve_authorization_request(
        self,
        request_id: int,
        approved_by: str,
    ) -> Optional[HyprlandAuthorizationRequest]:
        """Approve an authorization request."""
        request = await self.get_authorization_request(request_id)
        if not request:
            return None

        if request.status != "pending":
            raise ValueError(f"Request is not pending: {request.status}")

        request.status = "approved"
        request.approved_by = approved_by
        request.approved_at = datetime.now(UTC)
        request.updated_at = datetime.now(UTC)
        await self.db.flush()
        return request

    async def deny_authorization_request(
        self,
        request_id: int,
        denied_by: str,
        reason: str,
    ) -> Optional[HyprlandAuthorizationRequest]:
        """Deny an authorization request."""
        request = await self.get_authorization_request(request_id)
        if not request:
            return None

        if request.status != "pending":
            raise ValueError(f"Request is not pending: {request.status}")

        request.status = "denied"
        request.approved_by = denied_by
        request.approved_at = datetime.now(UTC)
        request.denied_reason = reason
        request.updated_at = datetime.now(UTC)
        await self.db.flush()
        return request

    async def list_authorization_requests(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        operator_id: Optional[str] = None,
    ) -> Tuple[List[HyprlandAuthorizationRequest], int]:
        """List authorization requests."""
        query = select(HyprlandAuthorizationRequest)
        count_query = select(func.count(HyprlandAuthorizationRequest.id))

        conditions = []
        if status:
            conditions.append(HyprlandAuthorizationRequest.status == status)
        if operator_id:
            conditions.append(HyprlandAuthorizationRequest.operator_id == operator_id)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(HyprlandAuthorizationRequest.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
