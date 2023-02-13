#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from datetime import datetime

import pytest
import requests
import xarray as xr

from weather_provider_api.routers.weather.sources.knmi.models.uurgegevens import UurgegevensModel
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


@pytest.fixture()
def start():
    today = datetime.today()
    year_to_use = today.year if today.month != 1 else (today.year - 1)  # This year if not January, else previous year
    return datetime(year_to_use, 1, 1)  # The start of the current year


@pytest.fixture()
def end():
    today = datetime.today()
    year_to_use = today.year if today.month != 1 else (today.year - 1)  # This year if not January, else previous year
    return datetime(year_to_use, 1, 31)  # The end of first month of the current year


def test_retrieve_weather(monkeypatch, mock_coordinates, start, end):
    mock_geoposition_coordinates = [GeoPosition(coordinate[0], coordinate[1]) for coordinate in mock_coordinates]
    # Version 3.x will be tested without an actual connection.
    uurgegevens_model = UurgegevensModel()
    ds = uurgegevens_model.get_weather(coords=mock_geoposition_coordinates, begin=start, end=end)

    assert ds is not None
    assert "TD" in ds
    assert isinstance(ds, xr.Dataset)

    # TEST 3: Test for HTTPError handling of non-200 status codes
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def mock_request_post(*args, **kwargs):
        return MockResponse({"dummy": "value"}, 404)

    monkeypatch.setattr(requests, "post", mock_request_post)

    with pytest.raises(requests.exceptions.HTTPError) as e:
        uurgegevens_model.get_weather(
            coords=mock_geoposition_coordinates,
            begin=start,
            end=end,
            weather_factors=None,
        )

    assert str(e.value.args[0]) == "Failed to retrieve data from the KNMI website"


def test__create_request_params():
    # If no weather factors are passed, the _create_request_params() function should return ["ALL"]
    # as the list of weather factors
    dag_model = UurgegevensModel()
    params_result = dag_model._create_request_params(
        datetime(2019, 4, 13), datetime(2019, 4, 18), ["DUMMYSTATION"], None
    )

    assert params_result["vars"] == "ALL"
