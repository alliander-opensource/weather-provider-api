#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from weather_provider_api.app.core.config import Config


def initialize_error_handling(app):
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)


# TODO: PRIORITY_2 -- Double-check the originally intended purpose for the request parameter here.
# (can it be replaced with _?)
async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """ This function translates an Exception into a JSONResponse holding information about the exception in question.

    If the flag "show_maintainer" is set to True, it will also display contact-information on whom to address related to
    the Exception.

    Args:
        request:    The original request that caused the Exception
        exc:        The exception to translate into a JSONResponse

    Returns:
        A JSONResponse object ready for use with the API
    """
    headers = getattr(exc, "headers", None)

    body = {"detail": exc.detail}
    if Config['show_maintainer']:
        body["maintainer"] = Config["app"]["maintainer"]
        body["maintainer_email"] = Config["app"]["maintainer_email"]

    return JSONResponse(body, status_code=exc.status_code, headers=headers)
