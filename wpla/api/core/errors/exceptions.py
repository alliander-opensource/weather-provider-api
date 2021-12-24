#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from typing import Any

from starlette.exceptions import HTTPException

"""API Specific Exceptions

This module holds all of the exceptions that were set up specifically for the WPLA API.

Note:
    The Exceptions for the WeatherController, WeatherSource and WeatherModel classes and their related functionality 
    have their own exceptions in /models/errors/exceptions.py
"""


class APIExpiredException(HTTPException):
    def __init__(self, detail: Any = None):
        self.detail = (
                detail or
                "This API has passed its expiry date and should be revalidated. Please contact the API maintainer"
        )
        self.status_code = 404
