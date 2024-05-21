#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import FastAPI
from starlette.exceptions import HTTPException

from weather_provider_api.configuration import API_CONFIGURATION
from weather_provider_api.core.handlers.exceptions import project_http_exception_handler
from weather_provider_api.core.handlers.rate_limiting import attach_rate_limiter
from weather_provider_api.routers.v3.router import v3_router

v3_application = FastAPI(
    version="0.1.0",
    title="Weather Provider API - Version 2 Interface",
    root_path="/v3",
    description=f"The health and liveliness interfaces for {API_CONFIGURATION.api_settings.full_title}",
    contact={"name": API_CONFIGURATION.maintainer.name, "email": API_CONFIGURATION.maintainer.email},
    servers=[{"url": f"{API_CONFIGURATION.api_settings.server_url}/v3"}],
    exception_handlers={HTTPException: project_http_exception_handler},
)

attach_rate_limiter(v3_application)
v3_application.include_router(v3_router, prefix="/v3")
v3_application.openapi()
