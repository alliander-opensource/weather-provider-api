#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""
==================
Metadata Extension
==================

The goal of this module is to add metadata about the API and if so configured, its maintainer to any generated page.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from wpla.configuration import Config


def initialize_metadata_header_middleware(app):
    """Function that adds the add_metadata_headers() function as middleware to an existing app"""
    async def add_metadata_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers['X-App-Version'] = Config['app']['version']
        response.headers['X-App-Valid-Till'] = Config['app']['valid_until'].strftime('%Y-%m-%d')
        if Config['show_maintainer']:
            response.headers['X-Maintainer'] = Config['app']['maintainer']
            response.headers['X-Maintainer-Email'] = Config['app']['maintainer_email']
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=add_metadata_headers)
