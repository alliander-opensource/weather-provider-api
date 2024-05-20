#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from datetime import UTC, datetime
from typing import re

from starlette.exceptions import HTTPException
from starlette.requests import Request

from weather_provider_api.configuration import API_CONFIGURATION


async def api_request_validator(request: Request, call_next):
    """Validate a request based on the API version in the URL."""
    if not __is_api_request_call(str(request.url)):
        return await call_next(request)

    if not __main_api_is_valid():
        raise HTTPException(status_code=400, detail="The main API is no longer valid.")

    if not __sub_api_is_valid(str(request)):
        raise HTTPException(status_code=400, detail="The sub-API is no longer valid.")

    return await call_next(request)


def __main_api_is_valid() -> bool:
    if datetime.now(UTC) > API_CONFIGURATION.api_settings.expiration_date:
        return False


def __sub_api_is_valid(url: str) -> bool:
    api_version_in_call = __get_api_version_from_url(url)
    if not api_version_in_call:
        raise HTTPException(status_code=400, detail="No API version found in the URL.")

    if datetime.now(UTC) > API_CONFIGURATION.sub_api_settings[api_version_in_call].expiration_date:
        return False

    return True


def __get_api_version_from_url(url: str) -> int | None:
    regex_to_search_for = r"\/v(\d+)\/"
    api_version_in_url = re.search(regex_to_search_for, url)

    if api_version_in_url and api_version_in_url.group(1).isdigit():
        return int(api_version_in_url.group(1))

    if api_version_in_url and not api_version_in_url.group(1).isdigit():
        raise HTTPException(status_code=400, detail="API version is not a number.")

    return None


def __is_api_request_call(url: str) -> bool:
    if __get_api_version_from_url(url):
        return True
    return False
