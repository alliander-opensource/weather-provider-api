#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, RedirectResponse

from weather_provider_api.configuration import API_CONFIGURATION
from weather_provider_api.core.handlers.exceptions import project_http_exception_handler
from weather_provider_api.core.handlers.logging import setup_included_project_logger
from weather_provider_api.core.utils.api_mounting_utils import mount_sub_application_to_base_application
from weather_provider_api.core.utils.verification import get_value_from_class_if_it_exists
from weather_provider_api.routers.health.app import health_application
from weather_provider_api.routers.utilities.app import utilities_application
from weather_provider_api.routers.v2.app import v2_application
from weather_provider_api.routers.v3.app import v3_application


def assemble_application_from_configuration() -> FastAPI:
    """Assemble the FastAPI application from the configuration settings."""
    application = __get_base_application()

    __attach_handlers(application)
    __attach_routers(application)

    __setup_redirects(application)

    return application


def __get_base_application() -> FastAPI:
    @asynccontextmanager
    async def lifespan(fastapi_application: FastAPI):
        """Set up the lifespan of the FastAPI application (replaces the old __on_event__ method)."""
        setup_included_project_logger()
        logging.info(
            f"Initial project logger set up for project "
            f"[{get_value_from_class_if_it_exists(fastapi_application, 'title')} "
            f"({get_value_from_class_if_it_exists(fastapi_application, 'version')})]."
        )

        yield

    application = FastAPI(
        title=API_CONFIGURATION.api_settings.full_title,
        description=API_CONFIGURATION.api_settings.description,
        version=API_CONFIGURATION.version,
        lifespan=lifespan,
        exception_handlers={HTTPException: project_http_exception_handler},
    )

    return application


def __attach_handlers(application: FastAPI):
    component_settings = API_CONFIGURATION.component_settings
    print("COMPONENT SETTINGS: ", component_settings)


def __attach_routers(application: FastAPI):
    connected_apis = API_CONFIGURATION.connected_apis

    __attach_administrative_routers(application)
    __attach_supported_api_version_routers(application, connected_apis)


def __attach_administrative_routers(application: FastAPI):
    mount_sub_application_to_base_application(base_application=application, sub_application=health_application)
    mount_sub_application_to_base_application(base_application=application, sub_application=utilities_application)


def __attach_supported_api_version_routers(application: FastAPI, connected_apis: list):
    for connected_api in connected_apis:
        if connected_api.version == 2:
            mount_sub_application_to_base_application(base_application=application, sub_application=v2_application)
        elif connected_api.version == 3:
            mount_sub_application_to_base_application(base_application=application, sub_application=v3_application)
        else:
            raise ValueError(f"Unsupported API version mentioned in configuration: {connected_api.version}")


def __setup_redirects(application: FastAPI):
    DEFAULT_API_VERSION = 2
    logging.info(f"Setting up default redirects to the main API version (v{DEFAULT_API_VERSION}).")

    @application.get("/", include_in_schema=False)
    async def redirect_to_default_api_version_docs():
        return RedirectResponse(url=f"/v{DEFAULT_API_VERSION}/docs")

    for connected_api in API_CONFIGURATION.connected_apis:
        application.add_api_route(
            f"/get_v{connected_api.version}_url", __create_endpoint(connected_api.version), methods=["GET"]
        )


def __create_endpoint(version: str):
    async def endpoint():
        return JSONResponse({"url": f"{API_CONFIGURATION.api_settings.server_url}/v{version}"})

    return endpoint
