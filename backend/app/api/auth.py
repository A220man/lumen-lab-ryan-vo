"""Auth API - placeholder for auth-oidc-keycloak feature."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/auth/login")
async def login():
    """Login - not yet implemented."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/auth/callback")
async def callback():
    """OIDC callback - not yet implemented."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/auth/logout")
async def logout():
    """Logout - not yet implemented."""
    raise HTTPException(status_code=501, detail="Not implemented")