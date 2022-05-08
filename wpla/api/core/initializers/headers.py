#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
==================
Metadata Header Extension
==================
The goal of this module is to add metadata about the API and if so configured, its maintainer to any generated page.
"""
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from wpla.configuration import app_config


def initialize_metadata_header_middleware(app):
    """Function that adds the add_metadata_headers() function as middleware to an existing app"""

    async def add_metadata_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-App-Version"] = app_config.version
        response.headers[
            "X-App-Valid-Till"
        ] = app_config.core_validation_date.strftime("%Y-%m-%d")
        if app_config.show_maintainer_info:
            response.headers["X-Maintainer"] = app_config.maintainer
            response.headers[
                "X-Maintainer-Email"
            ] = app_config.maintainer_email
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=add_metadata_headers)
    logger.info(
        f"Added Metadata Header extension middleware for: {app_config.name}"
    )
