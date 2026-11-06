"""Sandbox models for sandbox-orchestration feature."""

from datetime import datetime, UTC
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, JSON, Boolean
from sqlalchemy.orm import declarative_base

from app.services.database import Base


class SandboxStatus(str, Enum):
    """Sandbox status."""
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DELETED = "deleted"


class SandboxProvider(str, Enum):
    """Sandbox provider type."""
    LUME = "lume"
    QEMU = "qemu"
    FIRECRACKER = "firecracker"
    DOCKER = "docker"


class SandboxArchitecture(str, Enum):
    """Sandbox architecture (for ARM64 compatibility from issue #353)."""
    AMD64 = "amd64"
    ARM64 = "arm64"


class Sandbox(Base):
    """Sandbox model for cross-OS sandbox orchestration."""

    __tablename__ = "sandboxes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    provider = Column(SQLEnum(SandboxProvider), nullable=False, index=True)
    architecture = Column(SQLEnum(SandboxArchitecture), default=SandboxArchitecture.AMD64, nullable=False)
    status = Column(SQLEnum(SandboxStatus), default=SandboxStatus.CREATING, nullable=False, index=True)

    # Configuration
    image = Column(String(512), nullable=False)  # Docker image reference (GHCR from issue #22)
    cpu = Column(Integer, default=2, nullable=False)
    memory_mb = Column(Integer, default=4096, nullable=False)
    disk_gb = Column(Integer, default=20, nullable=False)

    # Network
    ports = Column(JSON, default=list, nullable=False)  # List of port mappings
    network_mode = Column(String(50), default="bridge", nullable=False)

    # Runtime info
    container_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    pid = Column(Integer, nullable=True)

    # Error info
    error_message = Column(Text, nullable=True)

    # Metadata
    labels = Column(JSON, default=dict, nullable=False)
    auto_remove = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)


class SandboxPortMapping(Base):
    """Port mapping for sandbox network configuration."""

    __tablename__ = "sandbox_port_mappings"

    id = Column(Integer, primary_key=True, index=True)
    sandbox_id = Column(Integer, nullable=False, index=True)
    host_port = Column(Integer, nullable=False)
    container_port = Column(Integer, nullable=False)
    protocol = Column(String(10), default="tcp", nullable=False)
    host_ip = Column(String(45), nullable=True)

