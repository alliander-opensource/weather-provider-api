#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from datetime import datetime

import pytest
import requests
import xarray as xr
from dateutil.relativedelta import relativedelta

from weather_provider_api.routers.weather.sources.knmi.models.pluim import PluimModel
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


@pytest.fixture()
def start():
    return datetime.utcnow()


@pytest.fixture()
def end():
    return datetime.utcnow() + relativedelta(days=15)


def test_retrieve_weather(monkeypatch, mock_coordinates, start, end):
    mock_geoposition_coordinates = [GeoPosition(coordinate[0], coordinate[1]) for coordinate in mock_coordinates]
    # TODO: Monkeypatch the download call to test without connection

    # TEST 1: Regular usage, with a non-existing factor
    pluim_model = PluimModel()
    # Factors contain both existing and non-existing factors. Non-existing factors should just be ignored..
    mock_factors = [
        "fake_factor_1",
        "wind_speed",
        "wind_direction",
        "short_time_wind_speed",
        "temperature",
        "precipitation",
        "cape",
    ]
    ds = pluim_model.get_weather(
        coords=mock_geoposition_coordinates,
        begin=start,
        end=end,
        weather_factors=mock_factors,
    )

    assert ds is not None
    assert "wind_speed" in ds
    assert "precipitation_sum" not in ds
    assert "fake_factor_1" not in ds
    assert isinstance(ds, xr.Dataset)

    # TEST 2: Empty list of weather factors should get the full set
    mock_factors = None
    ds = pluim_model.get_weather(
        coords=mock_geoposition_coordinates,
        begin=start,
        end=end,
        weather_factors=mock_factors,
    )

    assert ds is not None
    assert "wind_speed" in ds
    assert "precipitation_sum" in ds
    assert isinstance(ds, xr.Dataset)

    # TEST 3: Test for HTTPError handling of non-200 status codes
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def mock_request_get(self, *args, **kwargs):
        return MockResponse({"dummy": "value"}, 404)

    monkeypatch.setattr(requests, "get", mock_request_get)

    with pytest.raises(requests.exceptions.HTTPError) as e:
        pluim_model.get_weather(
            coords=mock_geoposition_coordinates,
            begin=start,
            end=end,
            weather_factors=mock_factors,
        )

    assert str(e.value.args[0])[:53] == "Failed to retrieve data from the KNMI website"
