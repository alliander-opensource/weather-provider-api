# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import locale
from datetime import datetime

import pytest
import requests  # type: ignore
import xarray as xr

from weather_provider_api.routers.weather.sources.knmi.models.actuele_waarnemingen import (
    ActueleWaarnemingenModel,
)
from weather_provider_api.routers.weather.sources.knmi.utils.commons import (
    _retrieve_observation_moment,  # type: ignore
    download_actuele_waarnemingen_weather,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


@pytest.fixture()
def start():
    """Fixture for providing a start datetime for the tests."""
    return datetime(2018, 1, 1)


@pytest.fixture()
def end():
    """Fixture for providing an end datetime for the tests."""
    return datetime(2018, 1, 31)


def test_get_weather(mock_coordinates: list[tuple[float, float]], start: datetime, end: datetime):
    """Test the get_weather function of the ActueleWaarnemingenModel for mock coordinates and a given time range."""
    mock_geo_coordinates = [GeoPosition(coordinate[0], coordinate[1]) for coordinate in mock_coordinates]
    aw_model = ActueleWaarnemingenModel()

    # TODO: Monkeypatch the download call to test without connection
    ds = aw_model.get_weather(coords=mock_geo_coordinates, begin=start, end=end)

    assert ds is not None
    assert "temperature" in ds
    assert len(ds["temperature"]) == 1
    assert isinstance(ds, xr.Dataset)


@pytest.mark.skip(reason="Test currently not working via Tox on GitHub Actions")
def test__retrieve_observation_date():
    """Test the _retrieve_observation_moment function for error handling and locale settings."""
    # Test to verify error handling
    current_locale = locale.getlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, "dutch")
    assert _retrieve_observation_moment(str(None)).date() == datetime.now().date()  # System now
    locale.setlocale(locale.LC_TIME, current_locale)


def test__download_weather(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the download_actuele_waarnemingen_weather function for error handling and successful download."""

    # Test to verify error handling for network/request issues
    def mock_request_get(*args, **kwargs):  # type: ignore
        raise requests.exceptions.RequestException("Fake RequestException!")

    monkeypatch.setattr(requests, "get", mock_request_get)  # type: ignore
    # The function now raises the exception, so we check for it
    import pytest

    with pytest.raises(requests.exceptions.RequestException):
        download_actuele_waarnemingen_weather()
