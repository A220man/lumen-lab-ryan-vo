"""Configuration settings for Lumen Lab."""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Lumen Lab"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Database
    database_url: str = "sqlite:///./lumen_lab.db"

    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "lumen-lab"
    keycloak_client_id: str = "lumen-lab-client"
    keycloak_client_secret: str = ""
    keycloak_admin_user: str = "admin"
    keycloak_admin_password: str = "admin"

    # LLM (optional)
    llm_provider: str = ""
    llm_model: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""

    # Benchmark defaults (from issue #3971)
    benchmark_observation_timeout_ms: int = 1000
    benchmark_settle_timeout_ms: int = 800
    benchmark_poll_interval_ms: int = 50


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()