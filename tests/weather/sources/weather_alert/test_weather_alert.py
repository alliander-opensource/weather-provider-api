# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import requests  # type: ignore
from requests.exceptions import ProxyError  # type: ignore

from weather_provider_api.weather.sources.weather_alert.weather_alert import (
    WeatherAlert,
)


def test_weather_alert_returns_all_province_statuses(monkeypatch: pytest.MonkeyPatch):
    """Return one parsed alert status per province without calling KNMI."""

    class FakeResponse:
        status_code = 200
        text = '<div class="alert alert--green"></div>'

    def fake_get(self, *args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "get", fake_get)

    wa = WeatherAlert()
    output = wa.get_alarm()

    assert len(output) == 12  # 1 response per province
    assert output[0][0] in (
        "drenthe",
        "friesland",
        "gelderland",
        "groningen",
        "flevoland",
        "limburg",
        "noord-brabant",
        "noord-holland",
        "overijssel",
        "utrecht",
        "zeeland",
        "zuid-holland",
    )
    assert all(status == "green" for _, status in output)


def test_weather_alert_errors(monkeypatch: pytest.MonkeyPatch):
    """Test the WeatherAlert class's error handling by simulating different exceptions during loading process."""
    wa = WeatherAlert()

    # Generating a fake ProxyError for the "_requests_retry_session.get" function
    class ProxyErrorSessionMock:
        def get(self, *args, **kwargs):  # type: ignore
            raise ProxyError("Fake Proxy Error!")

    class TimeoutSessionMock:
        def get(self, *args, **kwargs):  # type: ignore
            raise requests.Timeout("Fake Timeout Error!")

    class TooManyRedirectsSessionMock:
        def get(self, *args, **kwargs):  # type: ignore
            raise requests.TooManyRedirects("Fake Too Many Redirects Error!")

    class ConnectionErrorSessionMock:
        def get(self, *args, **kwargs):  # type: ignore
            raise requests.ConnectionError("Fake Connection Error!")

    # Testing Proxy Response
    monkeypatch.setattr(WeatherAlert, "_requests_retry_session", ProxyErrorSessionMock)

    output = wa.get_alarm()
    assert len(output) == 12  # Still 12 responses, but with proper error description inside..
    assert output[0][1] == "There was a proxy error while loading the page"

    # Testing Timeout Response
    monkeypatch.setattr(WeatherAlert, "_requests_retry_session", TimeoutSessionMock)

    output = wa.get_alarm()
    assert len(output) == 12  # Still 12 responses, but with proper error description inside..
    assert output[0][1] == "There was a timeout while loading the page"

    # Testing TooManyRedirects Response
    monkeypatch.setattr(WeatherAlert, "_requests_retry_session", TooManyRedirectsSessionMock)

    output = wa.get_alarm()
    assert len(output) == 12  # Still 12 responses, but with proper error description inside..
    assert output[0][1] == "The page proved inaccessible"

    monkeypatch.setattr(WeatherAlert, "_requests_retry_session", ConnectionErrorSessionMock)

    output = wa.get_alarm()
    assert len(output) == 12
    assert output[0][1] == "The page proved inaccessible"


def test_weather_alert_requests_have_connect_and_read_timeouts(monkeypatch: pytest.MonkeyPatch):
    """Every province request should have finite connect and read timeouts."""
    timeouts: list[tuple[float, float] | None] = []

    class FakeResponse:
        status_code = 200
        text = '<div class="alert alert--green"></div>'

    def fake_get(self, url, *args, **kwargs):
        timeouts.append(kwargs.get("timeout"))
        return FakeResponse()

    monkeypatch.setattr(requests.Session, "get", fake_get)

    output = WeatherAlert().get_alarm()

    assert len(output) == 12
    assert timeouts == [(2, 3)] * 12
    session = WeatherAlert._requests_retry_session()
    retry = session.get_adapter("https://").max_retries
    session.close()
    assert retry.total == 1
    assert retry.read == 0


# @pytest.mark.skip(reason="Monkeypatch for Response content not working properly. ")  # TODO: FIX
def test_weather_alert_wrongly_formatted_page(monkeypatch: pytest.MonkeyPatch):
    """Test the WeatherAlert class's handling of a wrongly formatted page by simulating unexpected content."""
    wa = WeatherAlert()

    def mock_request_response(_, *args, **kwargs) -> object:
        class FakeResponse:
            """A fake response object to simulate a wrongly formatted page."""

            status_code = 200
            text = "<HTML><BODY><DIV>Nothing Here!<DIV></BODY></HTML>"

        return FakeResponse()

    monkeypatch.setattr(requests.Session, "get", mock_request_response)  # Intercepting request response  # type: ignore
    output = wa.get_alarm()

    assert len(output) == 12  # Still 12 responses, but with proper error description inside..
    assert output[0][1] == "No weather alert code could be found on the page"
