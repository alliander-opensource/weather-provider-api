# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import asyncio

from weather_provider_api.app_version import APP_VERSION
from weather_provider_api.core.application import WPLA_APPLICATION


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
