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

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from wpla.api.core.errors.exceptions import APIExpiredException
from wpla.api.core.initializers.error_handling import handle_http_exception
from wpla.configuration import Config


def initialize_validation_middleware(app):
    """Function that adds API version validation as middleware to an existing app"""

    async def check_api_validity(request: Request, call_next):
        str_url = str(request.url)

        start_version_number = re.search(r"/api/v[0-9]+/weather", str_url).start() + 5
        end_version_number = re.search(r"/weather/", str_url).start()

        requested_api_version = str_url[start_version_number: end_version_number]
        now = datetime.now()

        valid_until = Config['app']['valid_until']
        version_valid_until = Config['app']['active_api_versions'][f'{requested_api_version}_valid_until']
        if now > valid_until:
            response = await handle_http_exception(request, APIExpiredException(
                f"The API's base environment has expired on {valid_until}. Please contact the maintainer!")
                                                   )
        elif now > version_valid_until:
            response = await handle_http_exception(request, APIExpiredException(
                f"API version [{requested_api_version}] has expired on {version_valid_until}. "
                "Please contact the maintainer!")
                                                   )
        else:
            response = await call_next(request)

        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=check_api_validity)
