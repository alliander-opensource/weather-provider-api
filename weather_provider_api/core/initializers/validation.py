# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""API Validation checks."""

import re
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from weather_provider_api.config import API_METADATA
from weather_provider_api.core.exceptions.exceptions import APIExpiredException
from weather_provider_api.core.initializers.exception_handling import (
    handle_http_exception,
)


def initialize_api_validation(application: FastAPI) -> None:
    """Method for attach the API validity checker to a FastAPI application.

    Args:
        application:    The FastAPI application to attach the checker to.

    Returns:
        Nothing. The application itself is updated.

    """

    async def check_api_for_validity(request: Request, call_next: Any) -> Any:
        """The method that validated the API validity.

        Args:
            request (Request): The request to evaluate.
            call_next (Any): Callable for the next middleware or endpoint.

        Returns:
            Any: The downstream response, or an error response when the API has expired.

        Raises:
            APIExpiredException: When raised while validating API expiration dates.

        """
        api_prefix = r"/api/v"
        api_suffix = "/weather"
        request_url = str(request.url)
        today = datetime.today().date()
        response = None

        api_version_in_url = re.search(f"{api_prefix}(\\d+){api_suffix}", request_url)

        if not api_version_in_url:
            return await call_next(request)  # No API call, no problem

        api_version_used = api_version_in_url.group(1)
        api_versions = {"1": API_METADATA.api_v1, "2": API_METADATA.api_v2}
        version_metadata = api_versions.get(api_version_used)
        if version_metadata is None:
            return await call_next(request)

        # Validate the base application
        base_expiration_date = API_METADATA.base_expiration_date
        if today > base_expiration_date:
            response = await handle_http_exception(
                request,
                APIExpiredException(
                    f"The main project's expiry date of [{base_expiration_date}] has been reached. "
                    "Please contact the maintainer of this project!"
                ),
            )

        # Validate the expiry date of the specific API version used
        version_expiration_date = version_metadata.expiration_date
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
