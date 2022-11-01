#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""Utilities for handling KNMI datasets.
"""
from typing import List

import numpy as np
import pandas as pd
from geopy.distance import great_circle

from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


def find_closest_stn_list(stn_stations: pd.DataFrame, coords: List[GeoPosition]):
    """
        A function that finds the closest stations to the locations in the given list of GeoPositions
    Args:
        stn_stations:   A Pandas Dataframe containing all of the station data for the KNMI stations
        coords:         A list of GeoPositions with locations to find the nearest stations to.
    Returns:
        A list of coordinates for found stations
        A list of found stations in the same order
        A list of index numbers for the found in the same order
    """
    _stn_stations = stn_stations.copy(deep=True)

    # get list of relevant STNs, choose closest STN
    coords_stn = [_find_closest_stn_single(_stn_stations, coord) for coord in coords]
    stns = list(set(coords_stn))
    coords_stn_ind = [stns.index(x) for x in coords_stn]
    return coords_stn, stns, coords_stn_ind


def _find_closest_stn_single(stn_stations: pd.DataFrame, coord: GeoPosition):
    """
        A function that finds the closest station to a single GeoPosition
    Args:
        stn_stations:   A Pandas Dataframe containing all of the station data for the KNMI stations
        coord:          A Geoposition to find the nearest station to.
    Returns:
        A station number indicating its index in the supplied dataframe.
    """
    stn_stations["distance"] = stn_stations.apply(
        lambda x: great_circle((x["lat"], x["lon"]), coord.get_WGS84()).km, axis=1
    )

    # Find the stn with the lowest distance to the location
    min_ind = np.argmin(stn_stations["distance"].values)
    # Return the found stn
    return stn_stations.loc[min_ind, "STN"]
