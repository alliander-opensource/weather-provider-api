# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import pytest

from weather_provider_api.routers.weather.utils.geo_position import (
    GeoCoordinateSystem,
    GeoPosition,
)
from weather_provider_api.routers.weather.utils.grid_helpers import (
    round_coordinates_to_wgs84_grid,
)


@pytest.mark.parametrize(
    "coordinates, grid_resolution_lat_lon, starting_points_lat_lon, expected_results",
    [
        (
            [GeoPosition(6.0, 9.0, GeoCoordinateSystem.WGS84)],
            (0.25, 0.25),
            (5.0, 10.0),
            [GeoPosition(6.0, 9.0, GeoCoordinateSystem.WGS84)],
        ),  # Already properly formatted
        (
            [GeoPosition(6.11, 9.22, GeoCoordinateSystem.WGS84)],
            (0.25, 0.25),
            (5.0, 10.0),
            [GeoPosition(6.0, 9.25, GeoCoordinateSystem.WGS84)],
        ),  # Rounding simple
        (
            [GeoPosition(-6, -9, GeoCoordinateSystem.WGS84)],
            (0.25, 0.25),
            (5.0, 10.0),
            [GeoPosition(-6, -9, GeoCoordinateSystem.WGS84)],
        ),  # Negative modifiers and before "starting point of grid"
        (
            [GeoPosition(7.112233444, 9.3423421233, GeoCoordinateSystem.WGS84)],
            (0.25, 0.25),
            (5.0, 10.0),
            [GeoPosition(7, 9.25, GeoCoordinateSystem.WGS84)],
        ),  # Extreme coordinate values
        (
            [GeoPosition(-6.92, -9.2, GeoCoordinateSystem.WGS84)],
            (0.125, 0.75),
            (5.0, 10.0),
            [GeoPosition(-6.875, -9.5, GeoCoordinateSystem.WGS84)],
        ),  # Negative modifiers and before "starting point of grid"
    ],
)
def test_round_to_grid(
    coordinates: list[GeoPosition],
    grid_resolution_lat_lon: tuple[float, float],
    starting_points_lat_lon: tuple[float, float],
    expected_results: list[GeoPosition],
) -> None:
    """Test the round_coordinates_to_wgs84_grid function for various coordinate values and grid configurations."""
    results = round_coordinates_to_wgs84_grid(coordinates, grid_resolution_lat_lon, starting_points_lat_lon)

    for result_coordinate, expected_result_coordinate in zip(results, expected_results, strict=False):
        assert result_coordinate.as_wgs84 == expected_result_coordinate.as_wgs84
