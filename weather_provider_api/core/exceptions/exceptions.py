#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel


class ExceptionResponseModel(BaseModel):
    """Class only used to relay the output for the HTTP Exception classes to the OpenAPI specification and
    Swagger UI.
    """

    detail: str


class APIExpiredException(HTTPException):
    def __init__(self, detail: Any = None):
        self.detail = (
            detail
            or "This API has passed it's expiry date and should be revalidated. Please contact the API maintainer."
        )
        self.status_code = 404
