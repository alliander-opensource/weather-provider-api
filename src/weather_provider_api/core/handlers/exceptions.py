#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request

from weather_provider_api.configuration import API_CONFIGURATION


async def project_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """The Project's HTTP Exception handler."""
    headers = getattr(exc, "headers", None)

    body = {"detail": exc.detail, "request": str(request.url)}

    if API_CONFIGURATION.maintainer.add_to_headers:
        body["maintainer"] = API_CONFIGURATION.maintainer.name
        body["maintainer_email"] = API_CONFIGURATION.maintainer.email_address

    return JSONResponse(content=body, status_code=exc.status_code, headers=headers)
