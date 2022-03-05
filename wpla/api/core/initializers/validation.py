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
        request_url = str(request.url)
        version_search_re = re.search(r"/api/v[0-9]+/", request_url)
        now = datetime.now()

        base_validation_date = Config['app']['valid_until']

        if now > base_validation_date:  # Check for validation date of the core application
            response = await handle_http_exception(request, APIExpiredException(
                f"This API's base environment support has expired on {base_validation_date}. "
                f"Please contact the API's maintainer or install a newer version."
            ))
        elif version_search_re is not None:
            requested_api_version = request_url[version_search_re.start() + 5: version_search_re.end() - 1]
            version_validation_date = Config['app']['active_api_versions'][f'{requested_api_version}_valid_until']
            if now > version_validation_date:
                response = await handle_http_exception(request, APIExpiredException(
                    f"The support for version [{requested_api_version}] has expired on {version_validation_date}. "
                    f"Please contact the API's maintainer or install a newer version."
                ))
            else:
                response = await call_next(request)
        else:
            response = await call_next(request)

        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=check_api_validity)
