# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0


import pandas as pd

from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


def coords_to_pd_index(coords: list[GeoPosition]) -> pd.MultiIndex:
    """Convert a list of GeoPosition objects to a pandas MultiIndex with WGS84 coordinates as tuples."""
    return pd.MultiIndex.from_tuples([coord.as_wgs84 for coord in coords], names=("lat", "lon"))
