#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from weather_provider_api.core.handlers.configuration_handler import WP_API_CONFIG


def install_exception_handler(app: FastAPI):
    """Install the custom exception handler into the FastAPI application.

    This function installs the custom exception handler into the FastAPI application.

    Args:
        app (FastAPI):
            The FastAPI application to install the exception handler into.

    """

    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        headers = getattr(exc, "headers", None)

        body = {"detail": exc.detail, "request": str(request.url)}

        if WP_API_CONFIG["maintainer"]["show_info"]:
            body["maintainer"] = WP_API_CONFIG["maintainer"]["name"]
            body["maintainer_email"] = WP_API_CONFIG["maintainer"]["email_address"]

        return JSONResponse(content=body, status_code=exc.status_code, headers=headers)

    app_title = app.title if hasattr(app, "title") else "Unknown"

    logger.info(f"WP API - init - Attaching Exception handler to:  {app_title}")
    # noinspection PyTypeChecker
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
