#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from typing import List, Tuple

import numpy as np

from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


def round_coordinates_to_wgs84_grid(
    coordinates: List[GeoPosition],
    grid_resolution_lat_lon: Tuple[float, float],
    starting_points_lat_lon: Tuple[float, float] = (0, 0),
) -> List[GeoPosition]:
    """A function that rounds coordinates to a WGS84 coordinate grid based on the given settings.

    Args:
        coordinates:                The list of coordinates to round to the grid.
        grid_resolution_lat_lon:    A tuple holding the grid resolution to use for rounding
        starting_points_lat_lon:    An optional tuple holding the starting values of the grid.
                                     Useful if a grid doesn't start at a multitude of the grid resolution.

    Returns:
        A list of coordinates that have been rounded to the nearest points on the given grid.

    """
    grid_res_lat = grid_resolution_lat_lon[0]
    grid_res_lon = grid_resolution_lat_lon[1]
    start_lat = starting_points_lat_lon[0]
    start_lon = starting_points_lat_lon[1]

    wgs84_coordinate_list = [coordinate.get_WGS84() for coordinate in coordinates]
    rounded_wgs84_coordinate_list = [
        (
            (np.round((coordinate[0] - start_lat) / grid_res_lat) * grid_res_lat) + start_lat,
            (np.round((coordinate[1] - start_lon) / grid_res_lon) * grid_res_lon) + start_lon,
        )
        for coordinate in wgs84_coordinate_list
    ]

    return [GeoPosition(coordinate[0], coordinate[1]) for coordinate in rounded_wgs84_coordinate_list]
