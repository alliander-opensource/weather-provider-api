#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from typing import Any

from fastapi import HTTPException


class APIExpiredException(HTTPException):
    def __init__(self, detail: Any = None):
        self.detail = (
            detail
            or "This API has passed it's expiry date and should be revalidated. "
            "Please contact the API maintainer."
        )
        self.status_code = 404
