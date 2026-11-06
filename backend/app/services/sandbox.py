"""Sandbox service for sandbox-orchestration feature."""

import asyncio
import uuid
from datetime import datetime, UTC
from typing import List, Optional, Tuple

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sandbox import Sandbox, SandboxStatus, SandboxProvider, SandboxArchitecture, SandboxPortMapping
from app.core.config import get_settings


class SandboxService:
    """Service for managing sandbox orchestration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def create_sandbox(
        self,
        name: str,
        provider: SandboxProvider,
        image: str,
        architecture: SandboxArchitecture = SandboxArchitecture.AMD64,
        cpu: int = 2,
        memory_mb: int = 4096,
        disk_gb: int = 20,
        ports: Optional[List[dict]] = None,
        network_mode: str = "bridge",
        labels: Optional[dict] = None,
        auto_remove: bool = True,
    ) -> Sandbox:
        """Create a new sandbox."""
        sandbox = Sandbox(
            name=name,
            provider=provider,
            architecture=architecture,
            image=image,
            cpu=cpu,
            memory_mb=memory_mb,
            disk_gb=disk_gb,
            ports=ports or [],
            network_mode=network_mode,
            labels=labels or {},
            auto_remove=auto_remove,
            status=SandboxStatus.CREATING,
        )
        self.db.add(sandbox)
        await self.db.commit()
        await self.db.refresh(sandbox)

        # Create port mappings
        if ports:
            for port_config in ports:
                mapping = SandboxPortMapping(
                    sandbox_id=sandbox.id,
                    host_port=port_config.get("host_port", 0),
                    container_port=port_config.get("container_port", 0),
                    protocol=port_config.get("protocol", "tcp"),
                    host_ip=port_config.get("host_ip"),
                )
                self.db.add(mapping)
            await self.db.commit()

        return sandbox

    async def get_sandbox(self, sandbox_id: int) -> Optional[Sandbox]:
        """Get a sandbox by ID."""
        result = await self.db.execute(select(Sandbox).where(Sandbox.id == sandbox_id))
        return result.scalar_one_or_none()

    async def list_sandboxes(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[SandboxStatus] = None,
        provider: Optional[SandboxProvider] = None,
        architecture: Optional[SandboxArchitecture] = None,
    ) -> Tuple[List[Sandbox], int]:
        """List sandboxes with pagination and filtering."""
        query = select(Sandbox)
        count_query = select(func.count(Sandbox.id))

        if status:
            query = query.where(Sandbox.status == status)
            count_query = count_query.where(Sandbox.status == status)
        if provider:
            query = query.where(Sandbox.provider == provider)
            count_query = count_query.where(Sandbox.provider == provider)
        if architecture:
            query = query.where(Sandbox.architecture == architecture)
            count_query = count_query.where(Sandbox.architecture == architecture)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        query = query.order_by(Sandbox.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def start_sandbox(self, sandbox_id: int) -> Sandbox:
        """Start a sandbox (simulated)."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            raise ValueError(f"Sandbox {sandbox_id} not found")

        if sandbox.status not in (SandboxStatus.CREATING, SandboxStatus.STOPPED):
            raise ValueError(f"Cannot start sandbox in status {sandbox.status}")

        sandbox.status = SandboxStatus.RUNNING
        sandbox.started_at = datetime.now(UTC)
        sandbox.container_id = f"sandbox-{uuid.uuid4().hex[:12]}"
        sandbox.ip_address = f"172.17.0.{sandbox_id + 100}"

        await self.db.commit()
        await self.db.refresh(sandbox)
        return sandbox

    async def stop_sandbox(self, sandbox_id: int) -> Sandbox:
        """Stop a sandbox."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            raise ValueError(f"Sandbox {sandbox_id} not found")

        if sandbox.status != SandboxStatus.RUNNING:
            raise ValueError(f"Cannot stop sandbox in status {sandbox.status}")

        sandbox.status = SandboxStatus.STOPPED
        sandbox.stopped_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(sandbox)
        return sandbox

    async def delete_sandbox(self, sandbox_id: int) -> bool:
        """Delete a sandbox."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            return False

        # Delete port mappings first
        await self.db.execute(delete(SandboxPortMapping).where(SandboxPortMapping.sandbox_id == sandbox_id))

        # Delete sandbox
        await self.db.delete(sandbox)
        await self.db.commit()
        return True

    async def get_port_mappings(self, sandbox_id: int) -> List[SandboxPortMapping]:
        """Get port mappings for a sandbox."""
        result = await self.db.execute(
            select(SandboxPortMapping).where(SandboxPortMapping.sandbox_id == sandbox_id)
        )
        return list(result.scalars().all())

