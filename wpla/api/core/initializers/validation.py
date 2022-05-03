#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""
######################
API Version Validation
######################
This module adds middleware that will check the API (sub-)versions for their validity based on their expiration dates.
Note:
    Not only the API versions themselves have a 'valid_until' date, but also the full application.
"""
import re
from datetime import datetime


from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from wpla.api.core.exceptions.exceptions import APIExpiredException
from wpla.api.core.initializers.exception_handling import handle_http_exception
from wpla.configuration import app_config


def initialize_validation_middleware(app):
    """Initialize the validation steps to be executed when running a request."""
    async def check_api_validity(request: Request, call_next):
        request_url = str(request.url)
        api_request_search = re.search(r"/api/v[0-9]+/weather", request_url)

        if api_request_search is None:
            # Not a API request call
            return await call_next(request)

        # Determine what the requested API (sub-)version was
        start_of_version_number = api_request_search.start() + 5
        end_of_version_number = re.search(r"/weather/", request_url).start()
        requested_api_version = request_url[
            start_of_version_number:end_of_version_number
        ]

        # Validate dates
        today = datetime.now().date()

        core_api_validation_date = app_config.core_validation_date
        api_subversion_validation_date = app_config.api_versions[
            requested_api_version
        ]["api_validation_date"]

        if core_api_validation_date < today:
            response = await handle_http_exception(
                request,
                APIExpiredException(
                    f"The core API environment has expired on {core_api_validation_date}. "
                    f"Please contact the maintainer."
                ),
            )
        elif api_subversion_validation_date < today:
            response = await handle_http_exception(
                request,
                APIExpiredException(
                    f"The environment for API request handler ({requested_api_version}) has expired on "
                    f"{api_subversion_validation_date}. Please contact the maintainer."
                ),
            )
        else:
            response = await call_next(request)

        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=check_api_validity)
    logger.info(f"Added API validation middleware for: {app_config.name}")
