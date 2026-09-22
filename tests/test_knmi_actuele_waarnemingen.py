# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import locale
from datetime import UTC, datetime
from types import SimpleNamespace

import numpy as np
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


@pytest.fixture
def start():
    """Fixture for providing a start datetime for the tests."""
    return datetime(2018, 1, 1)


@pytest.fixture
def end():
    """Fixture for providing an end datetime for the tests."""
    return datetime(2018, 1, 31)


@pytest.fixture
def observation_response():
        """Return a minimal KNMI observations page response."""
        html = """
        <table>
            <tr>
                <th>Station</th>
                <th>Weer</th>
                <th>Temp (°C)</th>
                <th>RV (%)</th>
                <th>Wind (bft)</th>
                <th>Wind (m/s)</th>
                <th>Zicht (m)</th>
                <th>Druk (hPa)</th>
            </tr>
            <tr>
                <td>Lelystad</td>
                <td>Bewolkt</td>
                <td>10.0</td>
                <td>80</td>
                <td>ZW</td>
                <td>4.0</td>
                <td>10000</td>
                <td>1015</td>
            </tr>
        </table>
        """
        return SimpleNamespace(ok=True, status_code=200, text=html)


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


@pytest.mark.parametrize(
    "observation_moment",
    [datetime(2026, 9, 22, 8, 0, tzinfo=UTC), datetime(2026, 9, 22, 8, 0)],
)
def test__download_weather_normalizes_observation_time(
    monkeypatch: pytest.MonkeyPatch, observation_response: SimpleNamespace, observation_moment: datetime
) -> None:
    """Test that aware and naive observation times become naive UTC timestamps."""
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: observation_response)
    monkeypatch.setattr(
        "weather_provider_api.routers.weather.sources.knmi.utils.commons._retrieve_observation_moment",
        lambda html_body: observation_moment,
    )

    dataset = download_actuele_waarnemingen_weather()

    assert dataset is not None
    assert dataset.time.dtype == np.dtype("datetime64[ns]")
    assert dataset.time.values[0] == np.datetime64("2026-09-22T08:00:00")


def test__retrieve_observation_moment_returns_aware_utc_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that locale failures return a timezone-aware UTC datetime."""
    def raise_locale_error(*args, **kwargs):  # type: ignore
        raise locale.Error("dutch locale unavailable")

    monkeypatch.setattr(locale, "setlocale", raise_locale_error)

    observation_moment = _retrieve_observation_moment("Waarnemingen 22 september 2026 08:00 uur")

    assert observation_moment.tzinfo == UTC


def test__download_weather_rejects_page_without_station_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a page without a station table raises an IndexError."""
    response = SimpleNamespace(ok=True, status_code=200, text="<table><tr><th>Unknown</th></tr></table>")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: response)

    with pytest.raises(IndexError, match="No table with 'Station' column found"):
        download_actuele_waarnemingen_weather()


def test__download_weather_returns_none_for_unsuccessful_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an unsuccessful KNMI response produces no dataset."""
    response = SimpleNamespace(ok=False, status_code=503, text="Service unavailable")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: response)

    assert download_actuele_waarnemingen_weather() is None


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
