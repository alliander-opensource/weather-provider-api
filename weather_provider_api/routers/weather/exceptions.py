#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from typing import Any

from fastapi import HTTPException


class UnknownSourceException(HTTPException):  # pragma: no cover
    def __init__(self, detail: Any = None):
        self.detail = detail or "unknown data source id"
        self.status_code = 404


class UnknownModelException(HTTPException):  # pragma: no cover
    def __init__(self, detail: Any = None):
        self.detail = detail or "unknown model id"
        self.status_code = 404


class UnknownDataTimeException(HTTPException):
    pass


class UnknownUnitException(HTTPException):
    pass
