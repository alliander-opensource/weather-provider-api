#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import structlog
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from wpla.configuration import Config

"""API Error Handling extension

This extended error handler reports information on the encountered exceptions, and if configured as such, information
on the maintainer and how to contact him/her/other as well.   
"""


logger = structlog.getLogger(__name__)


async def handle_http_exception(
        _: Request,
        exc: StarletteHTTPException
) -> JSONResponse:
    headers = getattr(exc, 'headers', None)

    body = {
        'detail': exc.detail
    }
    if Config['show_maintainer']:
        body['maintainer'] = Config['app']['maintainer']
        body['maintainer_email'] = Config['app']['maintainer_email']

    return JSONResponse(body, headers=headers, status_code=exc.status_code)


def initialize_error_handling(app):  # pragma: no cover
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
