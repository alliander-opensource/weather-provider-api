#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from typing import List

import pandas as pd

from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


def coords_to_pd_index(coords: List[GeoPosition]) -> pd.MultiIndex:
    return pd.MultiIndex.from_tuples([coord.get_WGS84() for coord in coords], names=("lat", "lon"))
