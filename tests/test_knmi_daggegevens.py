# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import datetime

import pytest
import requests  # type: ignore
import xarray as xr

from weather_provider_api.routers.weather.sources.knmi.models.daggegevens import (
    DagGegevensModel,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition

inseason_options = {True, False}


@pytest.fixture()
def start():
    return datetime(year=2019, month=1, day=1)


@pytest.fixture()
def end():
    return datetime(year=2019, month=1, day=31)


@pytest.mark.parametrize("inseason", inseason_options)
def test_retrieve_weather(mock_coordinates: list[tuple[float, float]], start: datetime, end: datetime, inseason: bool):
    mock_geoposition_coordinates = [GeoPosition(coordinate[0], coordinate[1]) for coordinate in mock_coordinates]
    # TODO: Monkeypatch the download call to test without connection
    daggegevens_model = DagGegevensModel()
    ds = daggegevens_model.get_weather(coords=mock_geoposition_coordinates, begin=start, end=end, inseason=inseason)

    print(ds["time"])
    assert ds is not None
    assert "TN" in ds
    assert len(ds["TN"]) in (30, 31)  # Temporal dimension length for test may vary depending on OS
    assert isinstance(ds, xr.Dataset)


def test__download_weather(monkeypatch: pytest.MonkeyPatch):
    # Test for HTTP exceptions
    dag_model = DagGegevensModel()

    class MockResponse:
        """A mock response class to simulate the behavior of requests.Response for testing purposes."""

        def __init__(self, json_data: dict[str, str], status_code: int):
            self.json_data = json_data
            self.status_code = status_code

        def json(self) -> dict[str, str]:
            """Return the JSON data of the mock response."""
            return self.json_data

    def mock_request_post(*args, **kwargs) -> MockResponse:  # type: ignore
        return MockResponse({"dummy": "value"}, 404)

    monkeypatch.setattr(requests, "post", mock_request_post)  # type: ignore

    with pytest.raises(requests.HTTPError) as e:
        assert dag_model._download_weather(  # type: ignore
            [1, 2],
            datetime(year=2020, month=3, day=1),
            datetime(year=2020, month=3, day=2),
            None,
            False,
        )
    assert str(e.value.args[0]) == "Failed to retrieve data from the KNMI website"
