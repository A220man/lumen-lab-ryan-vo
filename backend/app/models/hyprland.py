"""Hyprland models for hyprland-isolated-input feature."""

from datetime import datetime, UTC
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.services.database import Base


class HyprlandSeatStatus(str, Enum):
    """Synthetic seat status."""
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class HyprlandCapability(str, Enum):
    """Hyprland capability types."""
    INPUT_MOUSE = "input.mouse"
    INPUT_KEYBOARD = "input.keyboard"
    INPUT_TOUCH = "input.touch"
    OUTPUT_DISPLAY = "output.display"
    CLIPBOARD = "clipboard"
    DRAG_DROP = "drag_drop"


class HyprlandOperatorRole(str, Enum):
    """Operator authorization roles."""
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class HyprlandSeat(Base):
    """Synthetic seat configuration for Hyprland isolated input."""

    __tablename__ = "hyprland_seats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(SQLEnum(HyprlandSeatStatus), default=HyprlandSeatStatus.PENDING, nullable=False, index=True)

    # Seat configuration
    capabilities = Column(JSON, default=list, nullable=False)  # List of HyprlandCapability
    seat_name = Column(String(64), nullable=False, unique=True)  # Hyprland seat name (e.g., "seat1")
    udev_rules = Column(Text, nullable=True)  # Custom udev rules for device assignment

    # Authorization
    operator_id = Column(String(255), nullable=False, index=True)
    operator_role = Column(SQLEnum(HyprlandOperatorRole), default=HyprlandOperatorRole.OPERATOR, nullable=False)
    authorized_by = Column(String(255), nullable=True)  # Admin who authorized
    authorized_at = Column(DateTime, nullable=True)

    # Session limits
    max_session_duration_minutes = Column(Integer, default=60, nullable=False)
    idle_timeout_minutes = Column(Integer, default=10, nullable=False)

    # Metadata
    labels = Column(JSON, default=dict, nullable=False)
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    capability_negotiations = relationship("HyprlandCapabilityNegotiation", back_populates="seat", cascade="all, delete-orphan")


class HyprlandCapabilityNegotiation(Base):
    """Capability negotiation between operator and Hyprland compositor."""

    __tablename__ = "hyprland_capability_negotiations"

    id = Column(Integer, primary_key=True, index=True)
    seat_id = Column(Integer, ForeignKey("hyprland_seats.id"), nullable=False, index=True)

    # Requested capabilities
    requested_capabilities = Column(JSON, default=list, nullable=False)

    # Granted capabilities
    granted_capabilities = Column(JSON, default=list, nullable=False)

    # Negotiation state
    status = Column(String(50), default="pending", nullable=False)  # pending, granted, denied, expired
    negotiated_by = Column(String(255), nullable=True)  # Admin who negotiated

    # Protocol version
    protocol_version = Column(String(20), default="1.0", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Relationship
    seat = relationship("HyprlandSeat", back_populates="capability_negotiations")


class HyprlandAuthorizationRequest(Base):
    """Operator authorization request for Hyprland seat access."""

    __tablename__ = "hyprland_authorization_requests"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(String(255), nullable=False, index=True)
    seat_name = Column(String(64), nullable=False, index=True)

    # Request details
    requested_role = Column(SQLEnum(HyprlandOperatorRole), default=HyprlandOperatorRole.OPERATOR, nullable=False)
    requested_capabilities = Column(JSON, default=list, nullable=False)
    justification = Column(Text, nullable=True)

    # Approval
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, approved, denied, expired
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    denied_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime, nullable=True)
