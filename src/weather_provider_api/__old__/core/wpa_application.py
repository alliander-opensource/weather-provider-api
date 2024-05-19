#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import FastAPI
from loguru import logger
from starlette.responses import RedirectResponse

from weather_provider_api.core.handlers.configuration_handler import WP_API_CONFIG
from weather_provider_api.core.handlers.cors_handler import install_cors_handler
from weather_provider_api.core.handlers.exception_handler import install_exception_handler
from weather_provider_api.core.handlers.logging_handler import install_logging_handler
from weather_provider_api.core.handlers.prometheus_handler import install_prometheus_handler
from weather_provider_api.core.handlers.response_header_handler import install_response_header_handler
from weather_provider_api.core.handlers.validation_handler import install_api_validation_handler
from weather_provider_api.core.utils.api_mounting_utils import mount_fastapi_sub_app_to_app
from weather_provider_api.routing.versions.health import health_sub_app
from weather_provider_api.routing.versions.supporting import supporting_sub_app
from weather_provider_api.routing.versions.v2 import v2_sub_app
from weather_provider_api.routing.versions.v3 import v3_sub_app


def get_wpa_application() -> FastAPI:
    """Get the Weather Provider API application."""
    application_title = WP_API_CONFIG["base"].get("title", "Weather Provider API")
    application_description = WP_API_CONFIG["base"].get("description", "Weather Provider API")
    application_maintainer = WP_API_CONFIG["maintainer"].get("name", "Alliander N.V.")
    application_maintainer_email = WP_API_CONFIG["maintainer"].get("email_address", "weather.provider@alliander.com")



    # Initial application setup:
    from weather_provider_api.core.utils.version_detection import WP_API_APP_VERSION
    logger.info(f"WP API - init - Setting up application: {application_title} ({WP_API_APP_VERSION})")
    wpa_application = FastAPI(
        title=application_title,
        description=application_description,
        version=WP_API_APP_VERSION,
        contact={"name": application_maintainer, "email": application_maintainer_email},
    )

    # Attach requested configuration options:
    update_application_configuration_based_on_config(wpa_application)

    return wpa_application


def update_application_configuration_based_on_config(application: FastAPI):
    """Update the application handlers based on the configuration."""
    # Add the default handlers
    add_default_handlers(application)

    # Add optional additional handlers
    add_optional_handlers(application)

    # Mount the separate available API versions:
    mount_api_versions(application)

    # Add default redirects to the main API
    add_default_redirects(application)


def add_default_handlers(application: FastAPI):
    """Add default handlers to the application."""
    # Add the logging handler first
    install_logging_handler(application)
    # Then the rest
    install_exception_handler(application)
    install_response_header_handler(application)


def add_optional_handlers(application: FastAPI):
    """Add optional handlers to the application based on the configuration."""
    if WP_API_CONFIG["components"].get("cors", False):
        install_cors_handler(application)
    if WP_API_CONFIG["components"].get("prometheus", False):
        install_prometheus_handler(application)
    if WP_API_CONFIG["base"].get("expiration_checking", False):
        install_api_validation_handler(application)


def mount_api_versions(application: FastAPI):
    """Mount the separate available API versions onto the base application."""
    # Mount the separate available API versions:
    mount_fastapi_sub_app_to_app(base_application=application, sub_application=health_sub_app)  # Health endpoints
    mount_fastapi_sub_app_to_app(base_application=application, sub_application=supporting_sub_app)  # Support endpoints
    mount_fastapi_sub_app_to_app(base_application=application, sub_application=v2_sub_app)  # V2 endpoints
    mount_fastapi_sub_app_to_app(base_application=application, sub_application=v3_sub_app)  # V3 endpoints


def add_default_redirects(application: FastAPI):
    """Add default redirects to the main API."""
    logger.info("WP API - init - Adding default redirects to the main API")

    @application.get("/", include_in_schema=False)
    async def redirect_to_docs():
        return RedirectResponse(url="/v3/api/docs")
