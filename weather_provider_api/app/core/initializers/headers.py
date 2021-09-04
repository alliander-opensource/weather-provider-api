#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from weather_provider_api.app.core.config import Config


def initialize_metadata_header_middleware(app):
    """ This function initializes the metadata headers for the API's responses for the supplied app

    If the flag "show_maintainer" is set to True, it will also display contact-information on whom to address related to
    the response.
    """
    async def add_metadata_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-App-Version"] = Config["app"]["main_version"]
        response.headers["X-App-Valid-Till"] = Config["app"]["valid_date"]
        return response

    async def add_metadata_headers_with_maintainer(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-App-Version"] = Config["app"]["main_version"]
        response.headers["X-App-Valid-Till"] = Config["app"]["valid_date"]
        response.headers["X-Maintainer"] = Config["app"]["maintainer"]
        response.headers["X-Maintainer-Email"] = Config["app"]["maintainer_email"]
        return response

    if Config["show_maintainer"]:
        insertion_func = add_metadata_headers_with_maintainer
    else:
        insertion_func = add_metadata_headers

    app.add_middleware(BaseHTTPMiddleware, dispatch=insertion_func)
