#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Exceptions for the Libraries part of the project

This module holds Exception classes for the Libraries part of this project. Any Exceptions for the API part of the
project can be found there.

"""

from datetime import datetime
from typing import Any, Tuple, List

import numpy as np


class InvalidMeteoModelException(Exception):
    """Exception class for an Invalid MeteoModel"""
    def __init__(self, detail: Any = None):
        super().__init__(detail)
        self.detail = detail or "MeteoModel class is considered invalid"

    def __str__(self):
        return f"{self.detail}"


class InvalidMeteoSourceException(Exception):
    """Exception class for an Invalid MeteoSource"""
    def __init__(self, detail: Any = None):
        super().__init__(detail)
        self.detail = detail or "MeteoSource class is considered invalid"

    def __str__(self):
        return f"{self.detail}"


class ModelNotFoundException(Exception):
    """Exception class for when a MeteoModel cannot be found within the targeted MeteoSource"""
    def __init__(self, model_short_name: str, detail: Any = None):
        super().__init__(detail)
        self.model_name = model_short_name
        self.detail = (
            detail
            or f"MeteoModel [{model_short_name}] was not found within this source"
        )

    def __str__(self):
        return f"{self.detail}"


class TimeFrameOutOfBoundException(Exception):
    """Exception class for when an invalid timeframe was used to request data from a MeteoModel"""
    def __init__(
        self,
        model_short_name: str,
        time_frame: Tuple[datetime, datetime],
        time_bounds: Tuple[datetime, datetime],
        detail: Any = None,
    ):
        super().__init__(detail)
        self.model_name = model_short_name
        self.time_frame = time_frame
        self.time_bounds = time_bounds
        self.detail = (
            detail
            or f"The timeframe ({self.time_frame}) could not be trimmed to the bounds for MeteoModel "
            f"{self.model_name}: ({self.time_bounds})"
        )

    def __str__(self):
        return f"{self.detail}"


class LocationsOutOfBoundException(Exception):
    """Exception class for when an invalid location was used to request data from a MeteoModel"""
    def __init__(
        self,
        model_short_name: str,
        source_crs: str,
        target_crs: str,
        locations: List[Tuple[np.float64, np.float64]],
        detail: Any = None,
    ):
        super().__init__(detail)
        self.model_name = model_short_name
        self.source_crs = source_crs
        self.target_crs = target_crs
        self.locations = locations
        self.detail = (
            detail
            or f"The following location(s) was or were out of bounds: [{self.locations}]."
            f"The problems occurred while transforming the data from coordinate system "
            f'"{self.source_crs}" to "{self.target_crs}".'
        )

    def __str__(self):
        return f"{self.detail}"
