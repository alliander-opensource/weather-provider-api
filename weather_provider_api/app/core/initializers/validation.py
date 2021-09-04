#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from weather_provider_api.app.core.config import Config
from weather_provider_api.app.core.errors.exceptions import APIExpiredException
from weather_provider_api.app.core.initializers.error_handling import handle_http_exception


def initialize_validation_middleware(app):
    """ This function adds a middleware solution to have the API check if it should be revalidated, based on the passed
    revalidation date from the configuration.

    """
    valid_date = datetime.strptime(Config["app"]["valid_date"], "%Y-%m-%d")

    async def check_api_validity(request: Request, call_next):
        if datetime.now() > valid_date:
            response = await handle_http_exception(request, APIExpiredException())
        else:
            response = await call_next(request)

        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=check_api_validity)


def initialize_validation_api_version(versioned_app):
    """ This function adds a middleware solution to have an specific API version check if it should be revalidated,
    based on the passed revalidation date from the configuration.

    """
    version = versioned_app.root_path[versioned_app.root_path.rfind('v') + 1:]
    valid_date = datetime.strptime(Config["app"]["endpoints"][f"v{version}_valid_date"], "%Y-%m-%d")

    async def check_api_version_validity(request: Request, call_next):
        if datetime.now() > valid_date:
            response = await handle_http_exception(
                request,
                APIExpiredException(f"The API v{version} Endpoint has passed its expiry date and should be revalidated."
                                    "Please contact the API maintainer"))

        else:
            response = await call_next(request)

        return response

    versioned_app.add_middleware(BaseHTTPMiddleware, dispatch=check_api_version_validity)
