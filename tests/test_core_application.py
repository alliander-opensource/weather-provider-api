# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import asyncio

from weather_provider_api.app_version import APP_VERSION
from weather_provider_api.core.application import WPLA_APPLICATION
from weather_provider_api.routers.weather.sources.weather_alert.weather_alert import WeatherAlert


def test_application_metadata_and_mounted_routes() -> None:
    """Build the configured application with versioned API routes."""
    assert WPLA_APPLICATION.version == APP_VERSION
    assert WPLA_APPLICATION.openapi_version == "3.0.2"
    paths = {route.path for route in WPLA_APPLICATION.routes}
    assert "/" in paths
    assert "/api/v1" in paths
    assert "/api/v2" in paths


def test_application_root_redirect_and_lifespan() -> None:
    """Run application startup and verify the default documentation redirect."""
    root_route = next(route for route in WPLA_APPLICATION.routes if route.path == "/")

    async def exercise_application() -> object:
        async with WPLA_APPLICATION.router.lifespan_context(WPLA_APPLICATION):
            return root_route.endpoint()

    response = asyncio.run(exercise_application())

    assert response.status_code == 307
    assert response.headers["location"] == "/api/v2/docs"


def test_weather_alert_routes_enforce_default_rate_limit(monkeypatch) -> None:
    """Both mounted weather-alert routes should enforce the configured default limit."""
    monkeypatch.setattr(WeatherAlert, "get_alarm", lambda self: [])

    async def request_status(path: str, client_host: str) -> int:
        messages: list[dict[str, object]] = []
        request_sent = False

        async def receive() -> dict[str, object]:
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": b"", "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message: dict[str, object]) -> None:
            messages.append(message)

        await WPLA_APPLICATION(
            {
                "type": "http",
                "asgi": {"version": "3.0", "spec_version": "2.3"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": path,
                "raw_path": path.encode(),
                "query_string": b"",
                "root_path": "",
                "headers": [(b"host", b"testserver")],
                "client": (client_host, 12345),
                "server": ("testserver", 80),
            },
            receive,
            send,
        )
        response_start = next(message for message in messages if message["type"] == "http.response.start")
        return int(response_start["status"])

    async def exercise_routes() -> dict[str, list[int]]:
        return {
            path: [await request_status(path, client_host) for _ in range(6)]
            for path, client_host in (
                ("/api/v1/api/v1/weather/alarms/knmi", "192.0.2.1"),
                ("/api/v2/weather/alarms/knmi", "192.0.2.2"),
                ("/api/v2/weather/sources", "192.0.2.3"),
            )
        }

    statuses = asyncio.run(exercise_routes())

    assert statuses == {
        "/api/v1/api/v1/weather/alarms/knmi": [200, 200, 200, 200, 200, 429],
        "/api/v2/weather/alarms/knmi": [200, 200, 200, 200, 200, 429],
        "/api/v2/weather/sources": [200, 200, 200, 200, 200, 429],
    }
