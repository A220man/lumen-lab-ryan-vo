"""Hyprland API - placeholder for hyprland-isolated-input feature."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/hyprland/config")
async def get_hyprland_config():
    """Get Hyprland config - not yet implemented."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/hyprland/authorize")
async def authorize_hyprland():
    """Authorize Hyprland session - not yet implemented."""
    raise HTTPException(status_code=501, detail="Not implemented")