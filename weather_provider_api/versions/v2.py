# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from fastapi import FastAPI

from weather_provider_api.config import API_METADATA, APP_CONFIG
from weather_provider_api.routers.weather.api_view_v2 import v2_router

app = FastAPI(
    version=API_METADATA.api_v2.implementation,
    title="Weather API (v2)",
    root_path="/api/v2",
    servers=[{"url": "/api/v2"}],
    description="The v2 endpoint interface for the Weather Provider API",
    contact={
        "name": APP_CONFIG.MAINTAINER,
        "email": APP_CONFIG.EMAIL,
    },
)

app.openapi_version = "3.0.2"

app.include_router(v2_router, prefix="/weather")
app.openapi()
