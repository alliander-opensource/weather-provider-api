#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from enum import Enum


class GeoCoordinateSystem(str, Enum):
    RijksDriehoeksCoordinaten = 'rd'
    WGS84 = 'wgs84'
