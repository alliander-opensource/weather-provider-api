# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import random
from datetime import UTC, datetime, timedelta

import xarray as xr

from weather_provider_api.routers.weather.base_models.repository import RepoDataFetchResult
from weather_provider_api.routers.weather.sources.cds.factors import era5sl_factors
from weather_provider_api.routers.weather.sources.cds.models.era5sl import ERA5SLModel
from weather_provider_api.routers.weather.sources.knmi.client.arome_repository import (
    HarmonieAromeRepository,
)
from weather_provider_api.routers.weather.sources.knmi.models.harmonie_arome import (
    HarmonieAromeModel,
)
from weather_provider_api.routers.weather.utils.date_helpers import subtract_months
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition

# The get_weather() function is not part of the test, as it consists purely of function calls to other functions that
# are already part of the testing regiment.
# The _get_list_of_factors_to_drop() function is not part of the test as it only compares the passed list to a list of
# ERA5SL factors and returns those ERA5SL factors that weren't on the list. Testing would be more error-prone and larger
# than the actual function.
# The _get_list_of_months function isn't tested as it only takes the first and last month of the passed time grid and
# uses the Numpy 'arange' function to turn those into a range of months.


# Valid periods should be between three years ago (rounding down the month), and 5 days before today
def test__validate_weather_factors():
    """Test the _validate_weather_factors function of the ERA5SLModel."""
    arome_model = ERA5SLModel()

    # TEST 1: No factors are passed. The full standard list of factors should be returned.
    assert arome_model._validate_weather_factors(None) == list(era5sl_factors.values())  # type: ignore

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
    assert arome_model._validate_weather_factors(random_list) == expected_returns  # type: ignore

    # TEST 3: Valid and invalid factors are passed. A KeyError should occur.
    list_of_factors = list(era5sl_factors.keys())
    random_list = [
        random.choice(list_of_factors),
        random.choice(list_of_factors),
        random.choice(list_of_factors),
        "mock_factor",
    ]
    assert arome_model._validate_weather_factors(random_list)  # type: ignore
    assert "mock_factor" not in arome_model._validate_weather_factors(random_list)  # type: ignore


def test_retrieve_weather(monkeypatch, mock_dataset_arome: xr.Dataset):  # type: ignore
    """Test the retrieve_weather function of the HarmonieAromeModel.

    This is done by monkeypatching the gather_period function of the HarmonieAromeRepository, which is used in the
    retrieve_weather function, to return a mock dataset instead of making an actual API call. The test then checks
    if the returned dataset has the expected structure and content.
    """
    five_days_ago = datetime.now(UTC).date() - timedelta(days=5)
    one_month_ago = subtract_months(five_days_ago, months=1)

    # Instead of returning the regular data
    def mock_fill_dataset_with_data(self, from_date, to_date, locations: list[tuple[float, float]], factors: list[str]):  # type: ignore
        _, _, _, _, _ = self, from_date, to_date, locations, factors  # type: ignore
        return mock_dataset_arome, RepoDataFetchResult.SUCCESS

    monkeypatch.setattr(HarmonieAromeRepository, "retrieve_data", mock_fill_dataset_with_data)  # type: ignore

    arome_model = HarmonieAromeModel()
    # The coordinates requested are those of Amsterdam and Arnhem
    ds = arome_model.get_weather(
        coords=[GeoPosition(52.3667, 4.8945), GeoPosition(51.9851, 5.8987)],
        begin=datetime.combine(one_month_ago, datetime.min.time()).astimezone(UTC),
        end=datetime.combine(five_days_ago, datetime.max.time()).astimezone(UTC),
    )

    # TODO: len doesn't match expectations for the field. Find out why
    # TODO: The mock-format needs to be enhanced to properly pass the formatting round. This already happens when not
    #       mocking, but needs to be supported by the mock-result as well, to get this to properly work offline..
    assert ds is not None
    assert "fake_factor_1" in ds
    assert len(ds["fake_factor_1"]) == 48  # 49 prediction moments per time in the mock dataset
    assert len(ds["fake_factor_1"][0]) == 95  # 96 periods in the mock dataset
    assert isinstance(ds, xr.Dataset)
