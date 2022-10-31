#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.

# Not testing the abstract get_weather and is_async functions as they are implemented and defined outside this scope
# Also not testing because they are just return value functions (with at most basic math applied):
#  -celsius_to_kelvin, kelvin_to_celsius, tenth_celsius_to_kelvin
#  -normalize_tenths
#  -no_conversion
#  -percentage_to_frac
#  -kmh_to_ms
#  -dutch_wind_direction_to_degrees
# Finally _create_reverse_lookup isn't tested because it only reverses the human to si conversion

from datetime import datetime

import numpy as np
import pytest
import xarray as xr

from weather_provider_api.routers.weather.api_models import OutputUnit
from weather_provider_api.routers.weather.sources.knmi.models.actuele_waarnemingen import (
    ActueleWaarnemingenModel,
)
from weather_provider_api.routers.weather.sources.knmi.models.daggegevens import (
    DagGegevensModel,
)
from weather_provider_api.routers.weather.sources.knmi.models.pluim import PluimModel
from weather_provider_api.routers.weather.sources.knmi.models.uurgegevens import (
    UurgegevensModel,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.pandas_helpers import coords_to_pd_index


@pytest.fixture
def mock_single_value_dataset(mock_coordinates):
    mock_geoposition_coordinates = [
        GeoPosition(coordinate[0], coordinate[1]) for coordinate in mock_coordinates
    ]
    mock_factor = ["temperature", "precipitation", "mock_unknown_field"]
    timeline = [datetime.now()]
    coord_indices = coords_to_pd_index(mock_geoposition_coordinates)
    data_dict = {
        weather_factor: (
            ["time", "coord"],
            np.zeros(shape=(len(timeline), len(coord_indices)), dtype=np.float64),
        )
        for weather_factor in mock_factor
    }
    ds = xr.Dataset(
        data_vars=data_dict, coords={"time": timeline, "coord": coord_indices}
    )

    # Fill the single temperature value with 25 degrees Celsius
    ds["temperature"].data = [[np.float64(25), np.float64(25)]]

    # Fill the single precipitation value with 32 millimeters Celsius
    ds["precipitation"].data = [[np.float64(32), np.float64(32)]]

    # Fill the field to test the handling of unknown values with 66
    ds["mock_unknown_field"].data = [[np.float64(66), np.float64(66)]]
    return ds


def test_convert_names_and_units(mock_single_value_dataset):
    base_model = PluimModel()

    # For Pluim the original temperature format is Celsius.
    # Therefore, OutputUnit.original and OutputUnit.human should both be the original value.
    # OutputUnit.si should be Kelvin, however.
    assert (
        base_model.convert_names_and_units(
            mock_single_value_dataset, OutputUnit.original
        )["temperature"][0][0]
        == 25.0
    )
    assert (
        base_model.convert_names_and_units(mock_single_value_dataset, OutputUnit.si)[
            "temperature"
        ][0][0]
        == 298.15
    )
    assert (
        base_model.convert_names_and_units(mock_single_value_dataset, OutputUnit.human)[
            "temperature"
        ][0][0]
        == 25.0
    )

    # For Pluim the original precipitation format is mm.
    # Therefore, OutputUnit.original and OutputUnit.human should both be the original value.
    # OutputUnit.si should be m, however.
    assert (
        base_model.convert_names_and_units(
            mock_single_value_dataset, OutputUnit.original
        )["precipitation"][0][0]
        == 32
    )
    assert (
        base_model.convert_names_and_units(mock_single_value_dataset, OutputUnit.si)[
            "precipitation"
        ][0][0]
        == 0.032
    )
    assert (
        base_model.convert_names_and_units(mock_single_value_dataset, OutputUnit.human)[
            "precipitation"
        ][0][0]
        == 32
    )

    with pytest.raises(TypeError) as e:
        assert base_model.convert_names_and_units(
            mock_single_value_dataset, "MOCK_OUTPUT"
        )
    assert str(e.value.args[0]) == "Invalid OutputUnit"

    # If the field name isn't known in the model, there are no conversion functions and the values
    # are assumed to be as the original for all formats
    assert (
        base_model.convert_names_and_units(
            mock_single_value_dataset, OutputUnit.original
        )["mock_unknown_field"][0][0]
        == 66
    )
    assert (
        base_model.convert_names_and_units(mock_single_value_dataset, OutputUnit.si)[
            "mock_unknown_field"
        ][0][0]
        == 66
    )
    assert (
        base_model.convert_names_and_units(mock_single_value_dataset, OutputUnit.human)[
            "mock_unknown_field"
        ][0][0]
        == 66
    )


# The ERA5SL Model does not use the _request_weather_factors() function and therefore not used in the test cases
# The Harmonie Model is currently not in use, due to changes to the format.
def test__request_weather_factors():
    # GENERAL: For each test, some of (or part of) the factors has its capitalization altered from the regular format.
    # For any input the function should return the proper capitalization for that factor
    base_model = PluimModel()

    # TEST 1: An empty weather-factors list should return the default list for that model.
    # For Pluim that is: wind_speed, wind_direction, short_time_wind_speed, temperature, precipitation,
    #                    precipitation_sum, cape
    weather_factors_input = None
    assert base_model._request_weather_factors(weather_factors_input) == [
        "wind_speed",
        "wind_direction",
        "short_time_wind_speed",
        "temperature",
        "precipitation",
        "precipitation_sum",
        "cape",
    ]

    # TEST 2: A list consisting of only known weather-factors for that model should return identical to the input
    # NOTE: The order of the output can get scrambled, which is why we sort the output before comparing!
    weather_factors_input = ["wind_speed", "precipitation", "temperature"]
    assert sorted(base_model._request_weather_factors(weather_factors_input)) == [
        "precipitation",
        "temperature",
        "wind_speed",
    ]

    # TEST 3: Known and unknown factors
    # If using the Uurgegevens or Daggegevens models, a list consisting of both valid and invalid factors
    # should filter out the unknown factors and return only the know factors. Any other model should return the full
    # list of factors passed.
    # NOTE: As before the order of the output can get scrambled, which is why we sort the output before comparing!
    # NOTE 'duck_feathers' is always the non-existing factor.

    weather_factors_input = [
        "WIND_SPEED",
        "duck_feathers",
        "precipitation",
        "temperature",
    ]

    # Pluim - full return of factors,
    assert sorted(base_model._request_weather_factors(weather_factors_input)) == [
        "precipitation",
        "temperature",
        "wind_speed",
    ]

    # Daggegevens - return only known factors
    extra_model = DagGegevensModel()
    weather_factors_input = ["FHNH", "fxx", "duck_feathers", "T10NH"]
    assert sorted(extra_model._request_weather_factors(weather_factors_input)) == [
        "FHNH",
        "FXX",
        "T10NH",
    ]

    # Uurgegevens - return only known factors
    extra_model = UurgegevensModel()
    weather_factors_input = ["DDVEC", "T10N", "duck_feathers", "vv"]
    assert sorted(extra_model._request_weather_factors(weather_factors_input)) == [
        "DDVEC",
        "T10N",
        "VV",
    ]

    # ActueleWaarnemingen - return only known factors
    extra_model = ActueleWaarnemingenModel()
    weather_factors_input = [
        "weather_description",
        "visibility",
        "duck_feathers",
        "AIR_pressure",
    ]
    assert sorted(extra_model._request_weather_factors(weather_factors_input)) == [
        "air_pressure",
        "visibility",
        "weather_description",
    ]

    # TEST 4: Only unknown factors
    # All unknown factors should be removed from the list, leaving an empty list
    weather_factors_input = ["duck_feathers", "goose_FEATHERS"]
    assert sorted(base_model._request_weather_factors(weather_factors_input)) == []

    extra_model = DagGegevensModel()
    assert sorted(extra_model._request_weather_factors(weather_factors_input)) == []

    extra_model = UurgegevensModel()
    assert sorted(extra_model._request_weather_factors(weather_factors_input)) == []

    extra_model = ActueleWaarnemingenModel()
    assert sorted(extra_model._request_weather_factors(weather_factors_input)) == []


def test_knmi_visibility_class_to_meter_estimate():
    base_model = PluimModel()

    assert base_model.knmi_visibility_class_to_meter_estimate(49) == 4950
    assert base_model.knmi_visibility_class_to_meter_estimate(50) == 5500
    assert base_model.knmi_visibility_class_to_meter_estimate(51) == 1500
    assert (
        base_model.knmi_visibility_class_to_meter_estimate(88) == 72500
    )  # Odd, but correct?
    assert base_model.knmi_visibility_class_to_meter_estimate(89) == 70000


@pytest.mark.parametrize(
    "wind_direction,resulting_degrees",
    [
        ("N", 360.0),
        ("NNO", 22.5),
        ("NO", 45.0),
        ("ONO", 67.5),
        ("O", 90.0),
        ("OZO", 112.5),
        ("ZO", 135),
        ("ZZO", 157.5),
        ("Z", 180.0),
        ("ZZW", 202.5),
        ("ZW", 225.0),
        ("WZW", 247.5),
        ("W", 270.0),
        ("WNW", 292.5),
        ("NW", 315.0),
        ("NNW", 337.5),
        ("NOT_A_DIRECTION", None),
    ],
)
def test_dutch_wind_direction_to_degrees(wind_direction, resulting_degrees):
    base_model = PluimModel()
    assert (
        base_model.dutch_wind_direction_to_degrees(wind_direction) == resulting_degrees
    )
