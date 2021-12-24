#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from wpla.configuration import Config

"""Metadata Header extension

This module adds information on the API version, its expiry date and if so configured, its maintainer and where to 
contact him/her/other.
"""


def initialize_metadata_header_middleware(app):
    async def add_metadata_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers['X-App-Version'] = Config['app']['version']
        response.headers['X-App-Valid-Till'] = Config['app']['valid_until'].strftime('%Y-%m-%d')
        if Config['show_maintainer']:
            response.headers['X-Maintainer'] = Config['app']['maintainer']
            response.headers['X-Maintainer-Email'] = Config['app']['maintainer_email']
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=add_metadata_headers)
