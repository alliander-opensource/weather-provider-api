#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import structlog
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from weather_provider_api.app_config import get_setting

logger = structlog.get_logger(__name__)


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    headers = getattr(exc, "headers", None)

    body = {"detail": exc.detail}
    if get_setting("SHOW_MAINTAINER"):
        body["maintainer"] = get_setting("APP_MAINTAINER")
        body["maintainer_email"] = get_setting("APP_MAINTAINER_EMAIL")

    return JSONResponse(body, status_code=exc.status_code, headers=headers)


def initialize_error_handling(app):
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
