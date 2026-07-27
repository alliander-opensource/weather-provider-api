# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import pytest
import requests  # type: ignore
from requests.exceptions import ProxyError  # type: ignore

from weather_provider_api.routers.weather.sources.weather_alert.weather_alert import (
    WeatherAlert,
)


def test_weather_alert_():
    """Test the WeatherAlert class by calling the get_alarm method and checking the output format and content."""
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
    assert output[0][1] in (
        "green",
        "yellow",
        "orange",
        "red",
        "page didn't match",
        "page was inaccessible",
    )


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


# @pytest.mark.skip(reason="Monkeypatch for Response content not working properly. ")  # TODO: FIX
def test_weather_alert_wrongly_formatted_page(monkeypatch: pytest.MonkeyPatch):
    """Test the WeatherAlert class's handling of a wrongly formatted page by simulating unexpected content."""
    wa = WeatherAlert()

    def mock_request_response(_, nope: str = "") -> object:
        _ = nope  # Unused parameter to match the signature of the original function

        class FakeResponse:
            """A fake response object to simulate a wrongly formatted page."""

            status_code = 200
            text = "<HTML><BODY><DIV>Nothing Here!<DIV></BODY></HTML>"

        return FakeResponse()

    monkeypatch.setattr(requests.Session, "get", mock_request_response)  # Intercepting request response  # type: ignore
    output = wa.get_alarm()

    assert len(output) == 12  # Still 12 responses, but with proper error description inside..
    assert output[0][1] == "No weather alert code could be found on the page"
