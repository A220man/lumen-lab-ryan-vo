"""Sandboxes API - placeholder for sandbox-orchestration feature."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/sandboxes")
async def list_sandboxes():
    """List sandboxes - not yet implemented."""
    return {"items": [], "total": 0, "page": 1, "page_size": 20}

from fastapi import HTTPException

@router.post("/sandboxes")
async def create_sandbox():
    """Create sandbox - not yet implemented."""
    raise HTTPException(status_code=501, detail="Not implemented")