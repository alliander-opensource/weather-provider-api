# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime

import pytest
import requests  # type: ignore
import xarray as xr

from weather_provider_api.routers.weather.sources.knmi.models.uurgegevens import (
    UurgegevensModel,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


@pytest.fixture
def start():
    """Fixture for a start datetime, set to the beginning of the current year (or previous year if it's January)."""
    today = datetime.today()
    year_to_use = today.year if today.month != 1 else (today.year - 1)  # This year if not January, else previous year
    return datetime(year_to_use, 1, 1)  # The start of the current year


@pytest.fixture
def end():
    """Fixture for an end datetime.

    Set to the end of the first month of the current year (or previous year if it's January).
    """
    today = datetime.today()
    year_to_use = today.year if today.month != 1 else (today.year - 1)  # This year if not January, else previous year
    return datetime(year_to_use, 1, 31)  # The end of first month of the current year


def test_retrieve_weather(
    monkeypatch: pytest.MonkeyPatch, mock_coordinates: list[tuple[float, float]], start: datetime, end: datetime
):
    """Tests the get_weather function of the UurgegevensModel class."""
    mock_geoposition_coordinates = [GeoPosition(coordinate[0], coordinate[1]) for coordinate in mock_coordinates]
    # Version 3.x will be tested without an actual connection.
    uurgegevens_model = UurgegevensModel()
    ds = uurgegevens_model.get_weather(coords=mock_geoposition_coordinates, begin=start, end=end)

    assert ds is not None
    assert "TD" in ds
    assert isinstance(ds, xr.Dataset)

    # TEST 3: Test for HTTPError handling of non-200 status codes
    class MockResponse:
        def __init__(self, json_data: dict[str, str], status_code: int):
            """Mock response object for simulating requests responses."""
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            """Return the JSON data of the mock response."""
            return self.json_data

    def mock_request_post(*args, **kwargs):  # type: ignore
        """Mock function to replace requests.post, simulating a failed API call with a 404 status code."""
        return MockResponse({"dummy": "value"}, 404)

    monkeypatch.setattr(requests, "post", mock_request_post)  # type: ignore

    with pytest.raises(requests.exceptions.HTTPError) as e:
        uurgegevens_model.get_weather(
            coords=mock_geoposition_coordinates,
            begin=start,
            end=end,
            weather_factors=None,
        )

    assert str(e.value.args[0]) == "Failed to retrieve data from the KNMI website"


def test__create_request_params():
    """Tests the _create_request_params function of the UurgegevensModel class."""
    # If no weather factors are passed, the _create_request_params() function should return ["ALL"]
    # as the list of weather factors
    dag_model = UurgegevensModel()
    params_result = dag_model._create_request_params(  # type: ignore
        datetime(2019, 4, 13),
        datetime(2019, 4, 18),
        ["DUMMYSTATION"],
        None,  # type: ignore
    )

    assert params_result["vars"] == "ALL"
