#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""API Specific Exceptions

This handles the exceptions specific for the API part of the project.
Exceptions related to Libraries part of the project are kept there.

"""

from typing import Any

from starlette.exceptions import HTTPException


class APIExpiredException(HTTPException):
    """An Exception type that can be used when the main API or its versioned API components have expired."""

    def __init__(self, detail: Any = None):
        super().__init__(status_code=503, detail=detail)
        self.detail = (
            detail or "This API has passed its expiry date and should be revalidated. Please contact the API maintainer"
        )
        self.status_code = 503

    def __str__(self):
        return self.detail
