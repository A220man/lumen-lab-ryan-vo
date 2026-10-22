"""Benchmarks API - placeholder for driver-benchmark-api feature."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/benchmarks")
async def list_benchmarks():
    """List benchmarks - not yet implemented."""
    return {"items": [], "total": 0, "page": 1, "page_size": 20}


from fastapi import HTTPException

@router.post("/benchmarks")
async def create_benchmark():
    """Create benchmark - not yet implemented."""
    raise HTTPException(status_code=501, detail="Not implemented")