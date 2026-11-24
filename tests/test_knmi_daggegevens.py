# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
import requests  # type: ignore
import xarray as xr

from weather_provider_api.routers.weather.sources.knmi.models.daggegevens import (
    DagGegevensModel,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition

inseason_options = {True, False}


@pytest.fixture
def start():
    return datetime(year=2019, month=1, day=1)


@pytest.fixture
def end():
    return datetime(year=2019, month=1, day=31)


@pytest.mark.parametrize("inseason", inseason_options)
def test_retrieve_weather(
    monkeypatch: pytest.MonkeyPatch,
    mock_coordinates: list[tuple[float, float]],
    start: datetime,
    end: datetime,
    inseason: bool,
):
    """Parse synthetic KNMI daily observations without contacting the source."""
    mock_geoposition_coordinates = [GeoPosition(coordinate[0], coordinate[1]) for coordinate in mock_coordinates]

    def mock_request_post(*args, **kwargs):
        params = kwargs["data"]
        station_codes = [int(station) for station in params["stns"].split(":")]
        current_date = datetime.strptime(params["start"], "%Y%m%d").date()
        end_date = datetime.strptime(params["end"], "%Y%m%d").date()
        records = []
        while current_date <= end_date:
            records.extend(
                {"station_code": station, "date": current_date.isoformat(), "TN": 10}
                for station in station_codes
            )
            current_date += timedelta(days=1)
        return SimpleNamespace(status_code=200, text=json.dumps(records))

    monkeypatch.setattr(requests, "post", mock_request_post)  # type: ignore

    daggegevens_model = DagGegevensModel()
    ds = daggegevens_model.get_weather(coords=mock_geoposition_coordinates, begin=start, end=end, inseason=inseason)

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

    start = datetime(year=2020, month=3, day=1)
    end = datetime(year=2020, month=3, day=2)
    with pytest.raises(requests.HTTPError) as e:
        dag_model._download_weather(  # type: ignore
            [1, 2],
            start,
            end,
            None,
            False,
        )
    assert str(e.value.args[0]) == "Failed to retrieve data from the KNMI website"
