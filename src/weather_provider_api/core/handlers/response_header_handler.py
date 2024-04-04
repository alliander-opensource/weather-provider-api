#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from weather_provider_api.core.handlers.configuration_handler import WP_API_CONFIG
from weather_provider_api.core.utils.version_detection import WP_API_APP_VERSION


def install_response_header_handler(app: FastAPI):
    """Install the response header handler."""

    async def adjust_response_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-App-Version"] = WP_API_APP_VERSION
        response.headers["X-App-Name"] = WP_API_CONFIG["base"].get(
            "title", "Weather Provider API"
        )
        response.headers["X-App-Valid-Till"] = WP_API_CONFIG["base"]["expiration_date"]

        if WP_API_CONFIG["maintainer"].get("show_info", False):
            response.headers["X-Maintainer"] = WP_API_CONFIG["maintainer"].get(
                "name", "Maintainer Name Not Set!"
            )
            response.headers["X-Maintainer-Email"] = WP_API_CONFIG["maintainer"].get(
                "email_address", "Maintainer Email Not Set!"
            )
        return response
    logger.info("WP API - init - Installing response header handler.")
    app.add_middleware(BaseHTTPMiddleware, dispatch=adjust_response_headers)
