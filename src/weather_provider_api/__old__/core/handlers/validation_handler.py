#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import re
from datetime import datetime

from fastapi import FastAPI
from loguru import logger
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from weather_provider_api.core.handlers.configuration_handler import WP_API_CONFIG


def install_api_validation_handler(app: FastAPI):
    """Install the API validation middleware to the FastAPI application."""

    async def check_api_for_validity(request: Request, call_next):
        """Validate the main API and sub-API versions in the request URL based on their expiration dates."""
        validate_the_main_api()

        api_version_in_call = _get_api_version_from_url(str(request.url))
        if not api_version_in_call:
            return await call_next(request)  # A non-API call needs no validation

        validate_sub_api_version(api_version_in_call)

        # If the API is still valid, continue with the request
        return await call_next(request)

    logger.info("WP API - init - Attaching API validation middleware to the FastAPI application.")
    # noinspection PyTypeChecker
    app.add_middleware(BaseHTTPMiddleware, dispatch=check_api_for_validity)


def _get_api_version_from_url(url: str) -> str | None:
    """Retrieves the API version from a given URL if applicable.

    Args:
        url (str):
            A string representing the URL to search in.

    Returns:
        str | None:
            The API version if found, otherwise None.
    """
    regex_to_search_for = r"/api\/v(\d+)\/"
    api_version_in_url = re.search(regex_to_search_for, url)
    return api_version_in_url.group(1) if api_version_in_url else None


def validate_the_main_api():
    """Validate the main API based on its expiration date.

    Raises:
        HTTPException:
            If the main API has expired.
    """
    _expiration_date_string = WP_API_CONFIG["base"].get("expiration_date", "2099-12-31")
    try:
        main_api_expiration_date = datetime.strptime(_expiration_date_string, "%Y-%m-%d").date()
    except ValueError as val_error:
        raise ValueError(
            f"WP API - An invalid expiration date was set for the main API in the configuration file: "
            f"{_expiration_date_string}"
        ) from val_error

    if datetime.today().date() > main_api_expiration_date:
        raise HTTPException(
            status_code=406,
            detail=f"The main API has expired on [{main_api_expiration_date}]. "
            f"Please contact the API administrator for further information.",
        )


def validate_sub_api_version(api_version: str):
    """Validate a sub-API version based on its expiration date.

    Args:
        api_version (str):
            The version of the sub-API to validate.

    Raises:
        HTTPException:
            If the sub-API version has expired.
    """
    _sub_api_version_expiration_date_string = WP_API_CONFIG[f"api_v{api_version}"].get("expiration_date", "2099-12-31")

    try:
        sub_api_expiration_date = datetime.strptime(_sub_api_version_expiration_date_string, "%Y-%m-%d").date()
    except ValueError as val_error:
        raise ValueError(
            f"WP API - An invalid expiration date was set for API version [{api_version}] in the configuration file: "
            f"{_sub_api_version_expiration_date_string}"
        ) from val_error

    if datetime.today().date() > sub_api_expiration_date:
        raise HTTPException(
            status_code=406,
            detail=f"The API version [{api_version}] has expired on [{sub_api_expiration_date}]. "
            f"Please contact the API administrator for further information.",
        )
