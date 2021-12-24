#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from wpla.api.core.errors.exceptions import APIExpiredException
from wpla.api.core.initializers.error_handling import handle_http_exception
from wpla.configuration import Config

"""Add API Validation

This module adds the middleware that will check the API versions for their validity.

Note:
    Not only the API versions themselves have a 'valid_until' date, but also the full application.
    
TODO: Verify proper working of the generic expiry date
"""


def initialize_validation_middleware(app):
    validation_date = Config['app']['valid_until']

    async def check_api_validity(request: Request, call_next):
        if datetime.now() > validation_date:
            response = await handle_http_exception(request, APIExpiredException())
        else:
            response = await call_next(request)

        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=check_api_validity)
