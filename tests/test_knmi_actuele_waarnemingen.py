#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.

from datetime import datetime

import numpy as np
import pytest
import requests
import xarray as xr

from weather_provider_api.routers.weather.sources.knmi.models.actuele_waarnemingen import ActueleWaarnemingenModel
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


@pytest.fixture()
def start():
    return np.datetime64("2018-01-01")


@pytest.fixture()
def end():
    return np.datetime64("2018-01-31")


def test_get_weather(mock_coordinates, start, end):
    mock_geo_coordinates = [GeoPosition(coordinate[0], coordinate[1]) for coordinate in mock_coordinates]
    aw_model = ActueleWaarnemingenModel()

    # TODO: Monkeypatch the download call to test without connection
    ds = aw_model.get_weather(coords=mock_geo_coordinates, begin=start, end=end)

    assert ds is not None
    assert "temperature" in ds
    assert len(ds["temperature"]) == 1
    assert isinstance(ds, xr.Dataset)


def test__retrieve_observation_date():
    # Test to verify error handling
    aw_model = ActueleWaarnemingenModel()
    assert aw_model._retrieve_observation_date(None).date() == datetime.utcnow().date()


def test__download_weather(monkeypatch):
    # Test to verify error handling
    aw_model = ActueleWaarnemingenModel()

    def mock_request_get(self, *args, **kwargs):
        raise requests.exceptions.BaseHTTPError("Fake BaseHTTP Error!")

    monkeypatch.setattr(requests, "get", mock_request_get)
    assert aw_model._download_weather() is None
