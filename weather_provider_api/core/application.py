#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" Main Application """

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from starlette.responses import RedirectResponse

from weather_provider_api.app_version import APP_VERSION
from weather_provider_api.config import APP_CONFIG
from weather_provider_api.core.initializers.cors import initialize_cors_middleware
from weather_provider_api.core.initializers.exception_handling import initialize_exception_handler
from weather_provider_api.core.initializers.headers import initialize_header_metadata
from weather_provider_api.core.initializers.logging_handler import initialize_logging
from weather_provider_api.core.initializers.mounting import mount_api_version
from weather_provider_api.core.initializers.prometheus import initialize_prometheus_interface
from weather_provider_api.core.initializers.validation import initialize_api_validation

from weather_provider_api.versions.v1 import app as v1
from weather_provider_api.versions.v2 import app as v2


def _build_api_application() -> FastAPI:
    """The main method for building a standardized FastAPI application for use with for instance Uvicorn.

    Returns:
        FastAPI:    A FastAPI application with the full API hooked up and properly initialized.

    Notes:
        This method can also serve as an example for setting up your own version of this API with different settings.

    """
    app_title = APP_CONFIG["base"]["title"]
    app_description = APP_CONFIG["base"]["description"]

    # Setting up the base application
    application = FastAPI(
        version=APP_VERSION,
        title=app_title,
        description=app_description,
        contact={"name": APP_CONFIG["maintainer"]["name"], "email": APP_CONFIG["maintainer"]["email_address"]},
    )
    application.openapi_version = "3.0.2"

    # Attach logging
    application.add_event_handler("startup", initialize_logging)

    # Attach selected middleware
    initialize_exception_handler(application)
    initialize_header_metadata(application)
    if APP_CONFIG["base"]["expiration_checking"]:
        initialize_api_validation(application)
    if APP_CONFIG["components"]["prometheus"]:
        initialize_prometheus_interface(application)
    if APP_CONFIG["components"]["cors"]:
        initialize_cors_middleware(application)

    # Create and connect to end-points
    mount_api_version(application, v1)
    mount_api_version(application, v2)

    # Adding a redirect from the root of the application to our default view
    @application.get("/")
    def redirect_to_docs():
        """This function redirects the visitors to the default view from the application's base URL"""
        return RedirectResponse(url="/api/v2/docs")

    application.openapi()

    return application


# Application constant available for re-use, rather than re-initialization.
WPLA_APPLICATION = _build_api_application()
