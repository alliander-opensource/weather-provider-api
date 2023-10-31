#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" API Validation checks """

from datetime import datetime
import re

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from weather_provider_api.config import APP_CONFIG
from weather_provider_api.core.exceptions.exceptions import APIExpiredException
from weather_provider_api.core.initializers.exception_handling import (
    handle_http_exception,
)


def initialize_api_validation(application: FastAPI):
    """Method for attach the API validity checker to a FastAPI application.

    Args:
        application:    The FastAPI application to attach the checker to.
    Returns:
        Nothing. The application itself is updated.

    """

    async def check_api_for_validity(request: Request, call_next):
        """The method that validated the API validity.

        Args:
            request:    The request to evaluate
            call_next:  The call_next object for the request (what to do next if this step doesn't raise any exceptions)
        Returns:
            The next step to execute for this request. This is either the original call_next, or an
             HTTP Exception trigger for an APIExpiredException.

        """
        api_prefix = r"/api/v"
        api_suffix = "/weather"
        request_url = str(request.url)
        today = datetime.today().date()
        response = None

        api_version_in_url = re.search(f"{api_prefix}\\d+{api_suffix}", request_url)  # Looks for mentioning of version

        if not api_version_in_url:
            return await call_next(request)  # No API call, no problem

        # Validate the base application
        base_expiration_date = datetime.strptime(APP_CONFIG["base"]["expiration_date"], "%Y-%m-%d").date()
        if today > base_expiration_date:
            response = await handle_http_exception(
                request,
                APIExpiredException(
                    f"The main project's expiry date of [{base_expiration_date}] has been reached. "
                    "Please contact the maintainer of this project!"
                ),
            )

        if not api_version_in_url:
            return await call_next(request)  # continue as normal if no api version is involved

        # Determine the API interpreter version used and its expiry date
        start_location_of_version_number_in_url = api_version_in_url.start() + len(api_prefix)
        end_location_of_version_number_in_url = api_version_in_url.end() - len(api_suffix)

        api_version_used = request_url[start_location_of_version_number_in_url:end_location_of_version_number_in_url]

        # Validate the expiry date of the specific API version used
        version_expiration_date = datetime.strptime(
            APP_CONFIG[f"api_v{api_version_used}"]["expiration_date"], "%Y-%m-%d"
        ).date()
        if today > version_expiration_date:
            if not response:
                response = await handle_http_exception(
                    request,
                    APIExpiredException(
                        f"The expiry date for the v{api_version_used} interface of this API has been reached: "
                        f"[{version_expiration_date}] Please contact the maintainer of this project!"
                    ),
                )
            else:
                response = await handle_http_exception(
                    request,
                    APIExpiredException(
                        f"The expiry dates for both the main project [{base_expiration_date}] and the "
                        f"v{api_version_used} interface [{version_expiration_date}] of this API have been reached."
                        "Please contact the maintainer of this project!"
                    ),
                )

        # Handle the request normally if no expiry was triggered
        if not response:
            response = await call_next(request)

        return response

    application.add_middleware(BaseHTTPMiddleware, dispatch=check_api_for_validity)
    logger.info("Attached API Expiration Checking to the application...")
