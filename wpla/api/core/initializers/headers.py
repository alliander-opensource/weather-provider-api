#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
======================================
Header Metadata Enhancement Middleware
======================================

This module intercepts the regular response and enriches it with extra metadata like the project's version or the
 project maintainer's name and email address, if so configured.
"""
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from wpla.configuration import app_config


def initialize_metadata_header_middleware(app):
    """ This function defines the function to use to add extra meta-data headers and attaches it to the given app.

    Args:
        app:    The app to add the  middleware function to

    """
    async def add_metadata_headers(request: Request, call_next):
        """ This (sub-)function is the method that gets called to improve the meta-data of the request results before
         returning those back to the default process.

        Args:
            request:    The request to modify
            call_next:  The call_next procedure used to identify what the following step will be

        Returns:
            A response object ready for use with the next middleware

        """
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
