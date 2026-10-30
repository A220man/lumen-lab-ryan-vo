"""Lumen Lab - FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import health, benchmarks, sandboxes, hyprland, auth
from app.services.database import init_db, close_db
import app.models.benchmark  # noqa: F401 - register models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Lumen Lab",
        description="Scale computer-use 2.0 with open-source drivers, cross-OS sandboxes, and benchmarks",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(benchmarks.router, prefix="/api/v1", tags=["benchmarks"])
    app.include_router(sandboxes.router, prefix="/api/v1", tags=["sandboxes"])
    app.include_router(hyprland.router, prefix="/api/v1", tags=["hyprland"])
    app.include_router(auth.router, prefix="/api/v1", tags=["auth"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)