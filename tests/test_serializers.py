#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from enum import Enum

import pytest
import xarray as xr

from weather_provider_api.routers.weather.api_models import (
    ResponseFormat,
    WeatherContentRequestQuery,
)
from weather_provider_api.routers.weather.utils.serializers import return_file_or_text_response


class MockResponseFormat(str, Enum):
    mock_format = "mock_format"


@pytest.fixture()
def mock_response_query(mock_factors: list[str]) -> WeatherContentRequestQuery:
    result = WeatherContentRequestQuery(begin="2020-01-01", end="2020-02-02", lat=51.873419, lon=5.705929, factors=mock_factors)
    return result


@pytest.mark.parametrize("response_format", [response.value for response in ResponseFormat])
def test_file_or_text_response_regular(response_format: str, mock_coordinates: list[tuple[float, float]], mock_dataset: xr.Dataset, mock_response_query: WeatherContentRequestQuery):
    # Ensure no exception is raised for any valid response format
    try:
        return_file_or_text_response(
            mock_dataset,
            ResponseFormat(response_format),
            "knmi",
            "pluim",
            mock_response_query,
            mock_coordinates,
        )
    except Exception as e:
        pytest.fail(f"return_file_or_text_response raised an exception for format {response_format}: {e}")


def test_file_or_text_response_forged_response_format(
        monkeypatch: pytest.MonkeyPatch, mock_coordinates: list[tuple[float, float]], mock_dataset: xr.Dataset, mock_response_query: WeatherContentRequestQuery
        ):
    # TEST 1: Non-existing ResponseFormat is intercepted by Class
    with pytest.raises(ValueError) as e:
        return_file_or_text_response(
            mock_dataset,
            ResponseFormat("mock_format"),
            "knmi",
            "pluim",
            mock_response_query,
            mock_coordinates,
        )
    assert str(e.value.args[0]) == "'mock_format' is not a valid ResponseFormat"
