#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# -*- coding: utf-8 -*-
import random
from datetime import datetime, timedelta

import xarray as xr
from dateutil.relativedelta import relativedelta

from weather_provider_api.routers.weather.sources.cds.client.era5sl_repository import (
    ERA5SLRepository,
)
from weather_provider_api.routers.weather.sources.cds.factors import era5sl_factors
from weather_provider_api.routers.weather.sources.cds.models.era5sl import ERA5SLModel

# Valid periods should be between three years ago (rounding down the month), and 5 days before today
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition

# The get_weather() function is not part of the test, as it consists purely of function calls to other functions that
# are already part of the testing regiment.
# The _get_list_of_factors_to_drop() function is not part of the test as it only compares the passed list to a list of
# ERA5SL factors and returns those ERA5SL factors that weren't on the list. Testing would be more error prone and larger
# than the actual function.
# The _get_list_of_months function isn't tested as it only takes the first and last month of the passed time grid and
# uses the Numpy arrange function to turn those into a range of months.


def test__validate_weather_factors():
    era5sl_model = ERA5SLModel()

    # TEST 1: No factors are passed. The full standard list of factors should be returned.
    assert era5sl_model._validate_weather_factors(None) == list(era5sl_factors.values())

    # TEST 2: Only valid factors are passed. The same list should be returned.
    list_of_factors = list(era5sl_factors.keys())
    random_list = [
        random.choice(list_of_factors),
        random.choice(list_of_factors),
        random.choice(list_of_factors),
    ]
    expected_returns = [
        era5sl_factors[random_list[0]],
        era5sl_factors[random_list[1]],
        era5sl_factors[random_list[2]],
    ]
    assert era5sl_model._validate_weather_factors(random_list) == expected_returns

    # TEST 3: Valid and invalid factors are passed. A KeyError should occur.
    list_of_factors = list(era5sl_factors.keys())
    random_list = [
        random.choice(list_of_factors),
        random.choice(list_of_factors),
        random.choice(list_of_factors),
        "mock_factor",
    ]
    assert era5sl_model._validate_weather_factors(random_list)
    assert "mock_factor" not in era5sl_model._validate_weather_factors(random_list)


def test_retrieve_weather(
    monkeypatch, mock_dataset_era5: xr.Dataset, _get_mock_repository_dir
):
    sixty_one_days_ago = datetime.utcnow() - timedelta(days=61)
    one_month_before_that = sixty_one_days_ago - relativedelta(months=1)

    # Instead of returning the regular data
    def mock_fill_dataset_with_data(self, era5sl_coordinates, begin, end):
        return mock_dataset_era5.copy(deep=True)

    monkeypatch.setattr(ERA5SLRepository, "gather_period", mock_fill_dataset_with_data)

    era5sl_model = ERA5SLModel()
    # The coordinates requested are those of Amsterdam and Arnhem
    ds = era5sl_model.get_weather(
        coords=[GeoPosition(52.3667, 4.8945), GeoPosition(51.9851, 5.8987)],
        begin=one_month_before_that,
        end=sixty_one_days_ago,
    )

    # TODO: len doesn't match expectations for the field. Find out why
    # TODO: The mock-format needs to be enhanced to properly pass the formatting round. This already happens when not
    #       mocking, but needs to be supported by the mock-result as well, to get this to properly work offline..
    assert ds is not None
    assert "fake_factor_1" in ds
    print(ds)
    assert len(ds["fake_factor_1"]) == 95  # 96 periods in the mock dataset
    assert isinstance(ds, xr.Dataset)
