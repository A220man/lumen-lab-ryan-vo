"""Benchmarks API for driver-benchmark-api feature."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.services.database import get_db
from app.services.benchmark import BenchmarkService
from app.models.benchmark import BenchmarkRun, BenchmarkStatus

router = APIRouter()


class BenchmarkCreateRequest(BaseModel):
    """Request to create a new benchmark run."""
    name: str = Field(..., min_length=1, max_length=255, description="Benchmark name")
    driver: str = Field(..., min_length=1, max_length=100, description="Driver type (e.g., lume, qemu, firecracker)")
    observation_timeout_ms: Optional[int] = Field(None, ge=100, le=60000, description="Observation timeout in milliseconds")
    settle_timeout_ms: Optional[int] = Field(None, ge=100, le=60000, description="Settle timeout in milliseconds")
    poll_interval_ms: Optional[int] = Field(None, ge=10, le=5000, description="Poll interval in milliseconds")


class BenchmarkRunResponse(BaseModel):
    """Benchmark run response."""
    id: int
    name: str
    driver: str
    status: BenchmarkStatus
    observation_timeout_ms: int
    settle_timeout_ms: int
    poll_interval_ms: int
    iterations: int
    min_latency_ms: Optional[float]
    max_latency_ms: Optional[float]
    avg_latency_ms: Optional[float]
    p50_latency_ms: Optional[float]
    p95_latency_ms: Optional[float]
    p99_latency_ms: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

class BenchmarkListResponse(BaseModel):
    """Paginated benchmark list response."""
    items: List[BenchmarkRunResponse]
    total: int
    page: int
    page_size: int


@router.get("/benchmarks", response_model=BenchmarkListResponse)
async def list_benchmarks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[BenchmarkStatus] = Query(None, description="Filter by status"),
    driver: Optional[str] = Query(None, description="Filter by driver"),
    db: AsyncSession = Depends(get_db),
):
    """List benchmark runs with pagination and filtering."""
    service = BenchmarkService(db)
    items, total = await service.list_benchmarks(page=page, page_size=page_size, status=status, driver=driver)

    return BenchmarkListResponse(
        items=[BenchmarkRunResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/benchmarks", response_model=BenchmarkRunResponse, status_code=201)
async def create_benchmark(
    request: BenchmarkCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new benchmark run."""
    service = BenchmarkService(db)
    run = await service.create_benchmark(
        name=request.name,
        driver=request.driver,
        observation_timeout_ms=request.observation_timeout_ms,
        settle_timeout_ms=request.settle_timeout_ms,
        poll_interval_ms=request.poll_interval_ms,
    )
    return BenchmarkRunResponse.model_validate(run)


@router.get("/benchmarks/{benchmark_id}", response_model=BenchmarkRunResponse)
async def get_benchmark(
    benchmark_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a benchmark run by ID."""
    service = BenchmarkService(db)
    run = await service.get_benchmark(benchmark_id)
    if not run:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return BenchmarkRunResponse.model_validate(run)


@router.post("/benchmarks/{benchmark_id}/run", response_model=BenchmarkRunResponse)
async def run_benchmark(
    benchmark_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Run a benchmark."""
    service = BenchmarkService(db)
    try:
        run = await service.run_benchmark(benchmark_id)
        return BenchmarkRunResponse.model_validate(run)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/benchmarks/{benchmark_id}/cancel", response_model=BenchmarkRunResponse)
async def cancel_benchmark(
    benchmark_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running benchmark."""
    service = BenchmarkService(db)
    try:
        run = await service.cancel_benchmark(benchmark_id)
        return BenchmarkRunResponse.model_validate(run)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

