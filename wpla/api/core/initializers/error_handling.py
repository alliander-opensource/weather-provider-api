#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""
============================
API Error Handling extension
============================

This extended error handler reports back information on encountered exceptions, and if configured as such, information
on the maintainer and how to contact him/her/other as well.

The used format allows for tertiary parties and logging monitors to easily handle specific error situations.

"""
import structlog
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from wpla.configuration import Config


logger = structlog.getLogger(__name__)


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles exceptions by reformatting them for proper consistent API output. If the maintainer isn't hidden by the
    configuration, the maintainer's name and email address will be supplied as well to allow the requesting party to
    inform the maintainer of any mishaps or structural errors.
    """
    headers = getattr(exc, 'headers', None)
    body = {
        'detail': exc.detail,
        # TODO: Add more information on the requested data, but keep them optional based on the type of exception..
    }

    if Config['show_maintainer']:
        body['maintainer'] = Config['app']['maintainer']
        body['maintainer_email'] = Config['app']['maintainer_email']

    return JSONResponse(body, headers=headers, status_code=exc.status_code)


def initialize_error_handling(app):  # pragma: no cover
    """Function that adds the error handler to an existing app"""
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
