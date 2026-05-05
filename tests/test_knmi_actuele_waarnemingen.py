#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import locale
from datetime import datetime

import numpy as np
import pytest
import requests
import xarray as xr

from weather_provider_api.routers.weather.sources.knmi.models.actuele_waarnemingen import (
    ActueleWaarnemingenModel,
)
from weather_provider_api.routers.weather.sources.knmi.utils import (
    _retrieve_observation_moment,
    download_actuele_waarnemingen_weather,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


@pytest.fixture()
def start():
    return np.datetime64("2018-01-01")


@pytest.fixture()
def end():
    return np.datetime64("2018-01-31")


def test_get_weather(mock_coordinates: list[tuple[float, float]], start: np.datetime64, end: np.datetime64):
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
    # Test to verify error handling
    current_locale = locale.getlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, "dutch")
    assert _retrieve_observation_moment(str(None)).date() == datetime.now().date()  # System now
    locale.setlocale(locale.LC_TIME, current_locale)


def test__download_weather(monkeypatch: pytest.MonkeyPatch) -> None:
    # Test to verify error handling for network/request issues
    def mock_request_get(*args, **kwargs):
        raise requests.exceptions.RequestException("Fake RequestException!")

    monkeypatch.setattr(requests, "get", mock_request_get)
    # The function now raises the exception, so we check for it
    import pytest

    with pytest.raises(requests.exceptions.RequestException):
        download_actuele_waarnemingen_weather()
