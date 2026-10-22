"""Tests for configuration."""

import pytest
from app.core.config import Settings


def test_settings_defaults():
    """Test settings have correct defaults."""
    settings = Settings()
    assert settings.app_name == "Lumen Lab"
    assert settings.app_version == "1.0.0"
    assert settings.debug is False
    assert settings.environment == "development"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert "http://localhost:5173" in settings.cors_origins
    assert settings.database_url == "sqlite:///./lumen_lab.db"
    assert settings.keycloak_url == "http://localhost:8080"
    assert settings.keycloak_realm == "lumen-lab"
    assert settings.keycloak_client_id == "lumen-lab-client"
    assert settings.benchmark_observation_timeout_ms == 1000
    assert settings.benchmark_settle_timeout_ms == 800
    assert settings.benchmark_poll_interval_ms == 50


def test_settings_env_override(monkeypatch):
    """Test settings can be overridden by environment variables."""
    monkeypatch.setenv("APP_NAME", "Test Lab")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")

    settings = Settings()
    assert settings.app_name == "Test Lab"
    assert settings.debug is True
    assert settings.port == 9000