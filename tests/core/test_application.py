# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import asyncio

from fastapi.middleware.cors import CORSMiddleware

from weather_provider_api.app_version import APP_VERSION
from weather_provider_api.config.config import WPLASettings
from weather_provider_api.core import application as application_module
from weather_provider_api.core.application import WPLA_APPLICATION
from weather_provider_api.versions.v1 import app as v1
from weather_provider_api.versions.v2 import app as v2


def test_expiration_checking_defaults_enabled_and_can_be_overridden(monkeypatch) -> None:
    """Deployments may disable expiry checks explicitly, while the default remains enabled."""
    monkeypatch.delenv("ENABLE_EXPIRATION_CHECKING", raising=False)
    assert WPLASettings().ENABLE_EXPIRATION_CHECKING is True

    monkeypatch.setenv("ENABLE_EXPIRATION_CHECKING", "false")
    assert WPLASettings().ENABLE_EXPIRATION_CHECKING is False


def test_cors_is_disabled_by_default_and_can_be_configured(monkeypatch) -> None:
    """CORS stays off unless a deployment explicitly enables it with origins."""
    monkeypatch.delenv("ENABLE_CORS_HANDLING", raising=False)
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)
    settings = WPLASettings()
    assert settings.ENABLE_CORS_HANDLING is False
    assert settings.CORS_ALLOW_ORIGINS == []
    assert settings.CORS_ALLOW_CREDENTIALS is False
    assert settings.CORS_ALLOW_METHODS == ["GET"]
    assert settings.CORS_ALLOW_HEADERS == ["Accept"]

    monkeypatch.setenv("ENABLE_CORS_HANDLING", "true")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", '["https://weather.example.com"]')
    settings = WPLASettings()
    assert settings.ENABLE_CORS_HANDLING is True
    assert settings.CORS_ALLOW_ORIGINS == ["https://weather.example.com"]


def test_forwarded_allow_ips_defaults_to_loopback_and_can_be_overridden(monkeypatch) -> None:
    """Only local proxies are trusted by default, with deployment-specific override support."""
    monkeypatch.delenv("FORWARDED_ALLOW_IPS", raising=False)
    assert WPLASettings().FORWARDED_ALLOW_IPS == "127.0.0.1,::1"

    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "10.0.0.0/8")
    assert WPLASettings().FORWARDED_ALLOW_IPS == "10.0.0.0/8"


def test_application_metadata_and_mounted_routes() -> None:
    """Build the configured application with versioned API routes."""
    assert WPLA_APPLICATION.version == APP_VERSION
    assert WPLA_APPLICATION.openapi_version == "3.0.2"
    paths = {route.path for route in WPLA_APPLICATION.routes}
    assert "/" in paths
    assert "/api/v1" in paths
    assert "/api/v2" in paths
    assert "/health" in paths
    assert not any(m.cls is CORSMiddleware for m in WPLA_APPLICATION.user_middleware)
    assert v1.openapi()["servers"] == [{"url": "/api/v1"}]
    assert v2.openapi()["servers"] == [{"url": "/api/v2"}]


def test_health_endpoint_is_independent_of_prometheus(monkeypatch) -> None:
    """Container health remains available when the optional metrics endpoint is disabled."""
    monkeypatch.setattr(application_module.APP_CONFIG, "ENABLE_PROMETHEUS_SERVER", False)
    app = application_module._build_api_application()

    routes = {route.path: route for route in app.routes}
    assert "/health" in routes
    assert "/metrics" not in routes
    assert routes["/health"].endpoint() == {"status": "ok"}


def test_application_root_redirect_and_lifespan() -> None:
    """Run application startup and verify the default documentation redirect."""
    root_route = next(route for route in WPLA_APPLICATION.routes if route.path == "/")

    async def exercise_application() -> object:
        async with WPLA_APPLICATION.router.lifespan_context(WPLA_APPLICATION):
            return root_route.endpoint()

    response = asyncio.run(exercise_application())

    assert response.status_code == 307
    assert response.headers["location"] == "/api/v2/docs"
