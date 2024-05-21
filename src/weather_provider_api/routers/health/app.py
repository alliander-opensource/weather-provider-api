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
from weather_provider_api.routers.health.router import health_router

health_application = FastAPI(
    version="0.1.0",
    title="Weather Provider API - Health",
    root_path="/health",
    description=f"The health and liveliness interfaces for {API_CONFIGURATION.api_settings.full_title}",
    contact={"name": API_CONFIGURATION.maintainer.name, "email": API_CONFIGURATION.maintainer.email},
    servers=[{"url": f"{API_CONFIGURATION.api_settings.server_url}/health"}],
    exception_handlers={HTTPException: project_http_exception_handler},
)

attach_rate_limiter(health_application)
health_application.include_router(health_router, prefix="/health")
health_application.openapi()
