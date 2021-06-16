#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from typing import List, Optional

import numpy as np

from weather_provider_api.app.routers.weather.utils.geo_position import GeoPosition


def round_to_grid(
    coordinates: List[GeoPosition],
    grid_resolution_lat: float,
    grid_resolution_lon: float,
    lat_start_from: Optional[float] = 0,
    lon_start_from: Optional[float] = 0,
):
    wsg84_coords = [coord.get_WGS84() for coord in coordinates]
    wsg84_coords = [
        (
            (
                np.round((coord[0] - lat_start_from) / grid_resolution_lat)
                * grid_resolution_lat
            )
            + lat_start_from,
            (
                np.round((coord[1] - lon_start_from) / grid_resolution_lon)
                * grid_resolution_lon
            )
            + lon_start_from,
        )
        for coord in wsg84_coords
    ]

    return [GeoPosition(coord[0], coord[1]) for coord in wsg84_coords]
