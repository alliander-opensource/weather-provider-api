# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import pytest
from fastapi import HTTPException

from weather_provider_api.routers.weather.controller import WeatherController


@pytest.mark.parametrize(
    ("locations_string", "expected_coordinates"),
    [
        ("(52.1, 5.18)", [[(52.1, 5.18)]]),
        ("(-52.1, -5.18), (+52.2, 5.22)", [[(-52.1, -5.18)], [(52.2, 5.22)]]),
        ("  ( 52, 5 ) , ( .5, +10.25 )  ", [[(52.0, 5.0)], [(0.5, 10.25)]]),
    ],
)
def test_str_to_coords_parses_valid_coordinates(
    locations_string: str, expected_coordinates: list[list[tuple[float, float]]]
):
    """Parse signed coordinates and multiple coordinate pairs."""
    assert WeatherController.str_to_coords(locations_string) == expected_coordinates


@pytest.mark.parametrize("locations_string", ["", "not coordinates", "(52.1, 5.18) trailing", "(52.1)"])
def test_str_to_coords_rejects_malformed_coordinates(locations_string: str):
    """Reject malformed or incomplete coordinate input with a validation error."""
    with pytest.raises(HTTPException) as error:
        WeatherController.str_to_coords(locations_string)

    assert error.value.status_code == 422