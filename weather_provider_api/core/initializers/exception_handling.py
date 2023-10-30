#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastapi import FastAPI
from loguru import logger
#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from weather_provider_api.app_config import get_setting


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    headers = getattr(exc, "headers", None)

    body = {"detail": exc.detail, 'request': str(request.url)}
    if get_setting("SHOW_MAINTAINER"):
        body["maintainer"] = get_setting("APP_MAINTAINER")
        body["maintainer_email"] = get_setting("APP_MAINTAINER_EMAIL")

    return JSONResponse(body, status_code=exc.status_code, headers=headers)


def initialize_exception_handler(application: FastAPI):
    """ The method that attaches the customized exception handling method to a FastAPI application.

        Args:
            application:    The FastAPI application to attach the custom exception handler to.
        Returns:
            Nothing. The FastAPI application itself is updated.

        Notes:
            This method assumes that the FastAPI application given has a [title] set.

        TODO:
            Evaluate the dependency on [title] and [root_path] parameters being set for FastAPI applications in ALL
             initializers. By either extending the base class to enforce these or improving the code to not be dependent on
             these parameters, we can eradiate code smell and chances at Exceptions caused by not having these parameters.
        """
    application.add_exception_handler(StarletteHTTPException, handler=handle_http_exception)
    logger.info(f'Attached the Exception Handler to the application ({application.title})...')
