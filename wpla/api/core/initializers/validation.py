#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
=================================
API Version Validation Middleware
=================================

This module can add middleware to the project application that will check the main API and its sub-versions for
 validity based on any set expiry dates.

Notes:
    For this project both the main API and the available API sub-versions have their own expiry dates in the
     configuration.

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
    """ This function adds the middleware defined in the check_api_validity() to the given app.

    Args:
        app:    The application to mount the middleware onto

    Returns:
        Nothing

    """
    async def check_api_validity(request: Request, call_next):
        """ This function checks if the main API or its sub-application API components have expired.

        If it has, an APIExpiredException will be raised to prevent the API from running while unsupported

        Args:
            request:    The request to evaluate
            call_next:  The call_next procedure used to identify what the following step will be if everything is fine

        Returns:

        """
        request_url = str(request.url)
        api_request_search = re.search(r"/api/v\d+/weather", request_url)

        if api_request_search is None:
            # We only evaluate API request calls and can ignore everything else
            return await call_next(request)

        # Determine what the requested API (sub-)version was
        start_of_version_number = api_request_search.start() + 5
        end_of_version_number = re.search(r"/weather/", request_url).start()
        requested_api_version = request_url[
            start_of_version_number:end_of_version_number
        ]

        # Validate dates
        today = datetime.now().date()  # The start of today

        core_api_validation_date = app_config.core_validation_date  # The expiration date for the main API
        api_subversion_validation_date = app_config.api_versions[
            requested_api_version
        ]["api_validation_date"]  # The expiration date for the sub-version API used for the request

        if core_api_validation_date < today:
            # Handle main API validation
            response = await handle_http_exception(
                request,
                APIExpiredException(
                    f"The core API environment has expired on {core_api_validation_date}. "
                    f"Please contact the maintainer."
                ),
            )
        elif api_subversion_validation_date < today:
            # Handle sub-version API validation
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
