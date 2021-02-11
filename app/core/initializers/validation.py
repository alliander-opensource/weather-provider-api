#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.errors.exceptions import APIExpiredException
from app.core.initializers.error_handling import handle_http_exception
from app_config import get_setting


def initialize_validation_middleware(app):

    valid_date = datetime.datetime.strptime(get_setting("APP_VALID_DATE"), "%Y-%m-%d")

    async def check_api_validity(request: Request, call_next):
        if datetime.datetime.now() > valid_date:
            response = await handle_http_exception(request, APIExpiredException())
        else:
            response = await call_next(request)

        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=check_api_validity)
