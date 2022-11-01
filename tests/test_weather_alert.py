#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import requests
from requests.exceptions import ProxyError

from weather_provider_api.routers.weather.sources.weather_alert.weather_alert import (
    WeatherAlert,
)


def test_weather_alert_():
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
        "red",
        "page didn't match",
        "page was inaccessible",
    )


def test_weather_alert_errors(monkeypatch):
    wa = WeatherAlert()

    # Generating a fake ProxyError for the "_requests_retry_session.get" function
    class ProxyErrorSessionMock:
        def get(self, *args, **kwargs):
            raise ProxyError("Fake Proxy Error!")

    class TimeoutSessionMock:
        def get(self, *args, **kwargs):
            raise requests.Timeout("Fake Timeout Error!")

    class TooManyRedirectsSessionMock:
        def get(self, *args, **kwargs):
            raise requests.TooManyRedirects("Fake Too Many Redirects Error!")

    # Testing Proxy Response
    monkeypatch.setattr(WeatherAlert, "_requests_retry_session", ProxyErrorSessionMock)

    output = wa.get_alarm()
    assert (
        len(output) == 12
    )  # Still 12 responses, but with proper error description inside..
    assert output[0][1] == "proxy error on loading page"

    # Testing Timeout Response
    monkeypatch.setattr(WeatherAlert, "_requests_retry_session", TimeoutSessionMock)

    output = wa.get_alarm()
    assert (
        len(output) == 12
    )  # Still 12 responses, but with proper error description inside..
    assert output[0][1] == "time out op loading page"

    # Testing TooManyRedirects Response
    monkeypatch.setattr(
        WeatherAlert, "_requests_retry_session", TooManyRedirectsSessionMock
    )

    output = wa.get_alarm()
    assert (
        len(output) == 12
    )  # Still 12 responses, but with proper error description inside..
    assert output[0][1] == "page proved inaccessible"


# @pytest.mark.skip(reason="Monkeypatch for Response content not working properly. ")  # TODO: FIX
def test_weather_alert_wrongly_formatted_page(monkeypatch):
    wa = WeatherAlert()

    def mock_request_response(_, nope):
        class FakeResponse:
            status_code = 200
            text = "<HTML><BODY><DIV>Nothing Here!<DIV></BODY></HTML>"

        return FakeResponse()

    monkeypatch.setattr(
        requests.Session, "get", mock_request_response
    )  # Intercepting request response
    output = wa.get_alarm()

    assert (
        len(output) == 12
    )  # Still 12 responses, but with proper error description inside..
    assert output[0][1] == "could not find expected data on page"
