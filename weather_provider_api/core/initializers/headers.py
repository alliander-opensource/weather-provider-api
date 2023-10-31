#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0


from fastapi import FastAPI

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from weather_provider_api.app_version import APP_VERSION
from weather_provider_api.config import APP_CONFIG


def initialize_header_metadata(application: FastAPI):
    """Method that attaches the customized Metadata Header method that adds extra metadata.

    Args:
        application: The FastAPI application to attach the custom method to.
    Returns:
        Nothing. The FastAPI application itself is updated.
    """

    async def add_metadata_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-App-Version"] = APP_VERSION
        response.headers["X-App-Valid-Till"] = APP_CONFIG["base"]["expiration_date"]

        if APP_CONFIG["maintainer"]["show_info"]:
            response.headers["X-Maintainer"] = APP_CONFIG["maintainer"]["name"]
            response.headers["X-Maintainer-Email"] = APP_CONFIG["maintainer"]["email_address"]

        return response

    application.add_middleware(BaseHTTPMiddleware, dispatch=add_metadata_headers)
