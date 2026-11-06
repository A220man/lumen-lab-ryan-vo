"""Sandboxes API for sandbox-orchestration feature."""

from datetime import datetime, UTC
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import get_db
from app.services.sandbox import SandboxService
from app.models.sandbox import Sandbox, SandboxStatus, SandboxProvider, SandboxArchitecture, SandboxPortMapping

router = APIRouter()


class SandboxPortMappingRequest(BaseModel):
    """Port mapping request."""
    host_port: int = Field(..., ge=1, le=65535)
    container_port: int = Field(..., ge=1, le=65535)
    protocol: str = Field(default="tcp", pattern="^(tcp|udp)$")
    host_ip: Optional[str] = None


class SandboxPortMappingResponse(BaseModel):
    """Port mapping response."""
    id: int
    sandbox_id: int
    host_port: int
    container_port: int
    protocol: str
    host_ip: Optional[str] = None

    class Config:
        from_attributes = True


class SandboxCreateRequest(BaseModel):
    """Request to create a new sandbox."""
    name: str = Field(..., min_length=1, max_length=255)
    provider: SandboxProvider
    image: str = Field(..., min_length=1, max_length=512)
    architecture: SandboxArchitecture = SandboxArchitecture.AMD64
    cpu: int = Field(default=2, ge=1, le=128)
    memory_mb: int = Field(default=4096, ge=256, le=1048576)
    disk_gb: int = Field(default=20, ge=1, le=1000)
    ports: List[SandboxPortMappingRequest] = Field(default_factory=list)
    network_mode: str = Field(default="bridge", max_length=50)
    labels: dict = Field(default_factory=dict)
    auto_remove: bool = True


class SandboxUpdateRequest(BaseModel):
    """Request to update a sandbox."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    cpu: Optional[int] = Field(None, ge=1, le=128)
    memory_mb: Optional[int] = Field(None, ge=256, le=1048576)
    disk_gb: Optional[int] = Field(None, ge=1, le=1000)
    labels: Optional[dict] = None


class SandboxResponse(BaseModel):
    """Sandbox response."""
    id: int
    name: str
    provider: SandboxProvider
    architecture: SandboxArchitecture
    status: SandboxStatus
    image: str
    cpu: int
    memory_mb: int
    disk_gb: int
    ports: List[dict]
    network_mode: str
    container_id: Optional[str] = None
    ip_address: Optional[str] = None
    pid: Optional[int] = None
    error_message: Optional[str] = None
    labels: dict
    auto_remove: bool
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SandboxListResponse(BaseModel):
    """Paginated sandbox list response."""
    items: List[SandboxResponse]
    total: int
    page: int
    page_size: int


@router.get("/sandboxes", response_model=SandboxListResponse)
async def list_sandboxes(
    page: int = 1,
    page_size: int = 20,
    status: Optional[SandboxStatus] = None,
    provider: Optional[SandboxProvider] = None,
    architecture: Optional[SandboxArchitecture] = None,
    db: AsyncSession = Depends(get_db),
):
    """List sandboxes with pagination and filtering."""
    service = SandboxService(db)
    items, total = await service.list_sandboxes(
        page=page,
        page_size=page_size,
        status=status,
        provider=provider,
        architecture=architecture,
    )
    return SandboxListResponse(
        items=[SandboxResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/sandboxes", response_model=SandboxResponse, status_code=status.HTTP_201_CREATED)
async def create_sandbox(
    request: SandboxCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new sandbox."""
    service = SandboxService(db)
    sandbox = await service.create_sandbox(
        name=request.name,
        provider=request.provider,
        image=request.image,
        architecture=request.architecture,
        cpu=request.cpu,
        memory_mb=request.memory_mb,
        disk_gb=request.disk_gb,
        ports=[p.model_dump() for p in request.ports],
        network_mode=request.network_mode,
        labels=request.labels,
        auto_remove=request.auto_remove,
    )
    return SandboxResponse.model_validate(sandbox)


@router.get("/sandboxes/{sandbox_id}", response_model=SandboxResponse)
async def get_sandbox(
    sandbox_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a sandbox by ID."""
    service = SandboxService(db)
    sandbox = await service.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return SandboxResponse.model_validate(sandbox)


@router.patch("/sandboxes/{sandbox_id}", response_model=SandboxResponse)
async def update_sandbox(
    sandbox_id: int,
    request: SandboxUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a sandbox."""
    service = SandboxService(db)
    sandbox = await service.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sandbox, field, value)

    await db.commit()
    await db.refresh(sandbox)
    return SandboxResponse.model_validate(sandbox)


@router.post("/sandboxes/{sandbox_id}/start", response_model=SandboxResponse)
async def start_sandbox(
    sandbox_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Start a sandbox."""
    service = SandboxService(db)
    try:
        sandbox = await service.start_sandbox(sandbox_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SandboxResponse.model_validate(sandbox)


@router.post("/sandboxes/{sandbox_id}/stop", response_model=SandboxResponse)
async def stop_sandbox(
    sandbox_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Stop a sandbox."""
    service = SandboxService(db)
    try:
        sandbox = await service.stop_sandbox(sandbox_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SandboxResponse.model_validate(sandbox)


@router.delete("/sandboxes/{sandbox_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sandbox(
    sandbox_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a sandbox."""
    service = SandboxService(db)
    deleted = await service.delete_sandbox(sandbox_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sandbox not found")


@router.get("/sandboxes/{sandbox_id}/ports", response_model=List[SandboxPortMappingResponse])
async def get_sandbox_ports(
    sandbox_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get port mappings for a sandbox."""
    service = SandboxService(db)
    sandbox = await service.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    mappings = await service.get_port_mappings(sandbox_id)
    return [SandboxPortMappingResponse.model_validate(m) for m in mappings]
