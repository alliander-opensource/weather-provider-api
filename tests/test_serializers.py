# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from enum import StrEnum
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from weather_provider_api.routers.weather.api_models import (
    ResponseFormat,
    WeatherContentRequestQuery,
)
from weather_provider_api.routers.weather.utils.serializers import return_file_or_text_response


class MockResponseFormat(StrEnum):
    """A mock ResponseFormat for testing purposes."""

    mock_format = "mock_format"


@pytest.fixture
def mock_response_query(mock_factors: list[str]) -> WeatherContentRequestQuery:
    """Returns a mock WeatherContentRequestQuery for testing purposes."""
    result = WeatherContentRequestQuery(
        begin="2020-01-01", end="2020-02-02", lat=51.873419, lon=5.705929, factors=mock_factors
    )
    return result


@pytest.mark.parametrize("response_format", [response.value for response in ResponseFormat])
def test_file_or_text_response_regular(
    response_format: str,
    mock_coordinates: list[tuple[float, float]],
    mock_dataset: xr.Dataset,
    mock_response_query: WeatherContentRequestQuery,
):
    """Test the return_file_or_text_response function with all valid ResponseFormats."""
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
    monkeypatch: pytest.MonkeyPatch,
    mock_coordinates: list[tuple[float, float]],
    mock_dataset: xr.Dataset,
    mock_response_query: WeatherContentRequestQuery,
):
    # TEST 1: Non-existing ResponseFormat is intercepted by Class
    class FakeEnum(StrEnum):
        """A fake enum for testing purposes."""
        fake_format = "fake_format"
    response_format = FakeEnum.fake_format

    with pytest.raises(NotImplementedError) as e:
        return_file_or_text_response(
            mock_dataset,
            response_format,  # type: ignore[arg-type]
            "knmi",
            "pluim",
            mock_response_query,
            mock_coordinates,
        )
    assert str(e.value.args[0]) == f"Cannot create response for the {response_format} response format"


def test_file_or_text_response_netcdf4_with_timezone_aware_time(
    mock_coordinates: list[tuple[float, float]],
    mock_response_query: WeatherContentRequestQuery,
):
    """Test that NetCDF export succeeds when the dataset contains timezone-aware time coordinates."""
    timezone_aware_timeline = pd.date_range("2026-01-01", periods=4, freq="1h", tz="UTC")
    dataset = xr.Dataset(
        data_vars={"temperature": (["time", "lat", "lon"], np.zeros((4, 1, 1), dtype=np.float64))},
        coords={"time": timezone_aware_timeline, "lat": [mock_coordinates[0][0]], "lon": [mock_coordinates[0][1]]},
    )

    response, file_path = return_file_or_text_response(
        dataset,
        ResponseFormat.netcdf4,
        "cds",
        "era5sl",
        mock_response_query,
        mock_coordinates,
    )

    assert response is not None
    assert file_path is not None
    assert Path(file_path).exists()

    with xr.open_dataset(file_path, engine="netcdf4") as loaded_dataset:  # type: ignore
        assert "time" in loaded_dataset.coords
        assert "UTC" not in str(loaded_dataset.time.dtype)

    Path(file_path).unlink(missing_ok=True)
