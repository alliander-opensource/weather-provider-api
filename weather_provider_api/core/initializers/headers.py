#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from weather_provider_api.app_config import get_setting


def initialize_metadata_header_middleware(app):
    async def add_metadata_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-App-Version"] = get_setting("APP_VERSION")
        response.headers["X-App-Valid-Till"] = get_setting("APP_VALID_DATE")
        return response

    async def add_metadata_headers_with_maintainer(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-App-Version"] = get_setting("APP_VERSION")
        response.headers["X-App-Valid-Till"] = get_setting("APP_VALID_DATE")
        response.headers["X-Maintainer"] = get_setting("APP_MAINTAINER")
        response.headers["X-Maintainer-Email"] = get_setting("APP_MAINTAINER_EMAIL")
        return response

    show_maintainer = get_setting("SHOW_MAINTAINER")
    if show_maintainer:
        insertion_func = add_metadata_headers_with_maintainer
    else:
        insertion_func = add_metadata_headers

    app.add_middleware(BaseHTTPMiddleware, dispatch=insertion_func)
