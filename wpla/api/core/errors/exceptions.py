#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""
==============
API Exceptions
==============

This is where the WPLA API specific exceptions and errors are set up.

Note:
    This only holds the exceptions and errors for the API itself. Errors and Exceptions for the WeatherController,
    WeatherSource and WeatherModel classes (as well as those for any related functionality) are described in
    :mod:wpla.models.errors.exceptions
"""

from typing import Any

from starlette.exceptions import HTTPException


class APIExpiredException(HTTPException):
    """Exception for the expiration of the main API or its versioned API components
    """
    def __init__(self, detail: Any = None):
        self.detail = (
                detail or
                "This API has passed its expiry date and should be revalidated. Please contact the API maintainer"
        )
        self.status_code = 404
