#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from dateutil.relativedelta import relativedelta

from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.pandas_helpers import coords_to_pd_index


@pytest.fixture(scope="session")
def _get_mock_repository_dir():
    return Path(tempfile.gettempdir()).joinpath("PyTest_REPO")


@pytest.fixture(scope="session")
def mock_coordinates():
    return [(51.873419, 5.705929), (53.2194, 6.5665)]


@pytest.fixture(scope="session")
def mock_factors():
    return [
        "fake_factor_1",
        "fake_factor_2",
        "fake_factor_3",
        "fake_factor_4",
        "fake_factor_5",
    ]


@pytest.fixture(scope="session")
def mock_dataset(mock_coordinates, mock_factors):
    """
        returns a mock Xarray Dataset for
    Args:
        mock_coordinates:
        mock_factors:

    Returns:

    """
    timeline = pd.date_range(end=datetime.utcnow(), periods=96, freq="1H", inclusive="left")
    coord_indices = coords_to_pd_index([GeoPosition(51.873419, 5.705929), GeoPosition(53.2194, 6.5665)])
    weather_factors = mock_factors
    data_dict = {
        weather_factor: (
            ["time", "coord"],
            np.zeros(shape=(len(timeline), len(coord_indices)), dtype=np.float64),
        )
        for weather_factor in weather_factors
    }
    ds = xr.Dataset(data_vars=data_dict, coords={"time": timeline, "coord": coord_indices})
    ds = ds.unstack("coord")
    return ds


@pytest.fixture(scope="session")
def mock_dataset_era5(mock_coordinates, mock_factors):
    """
        returns a mock Xarray Dataset for
    Args:
        mock_coordinates:
        mock_factors:

    Returns:

    """
    timeline = pd.date_range(
        end=(datetime.utcnow() - relativedelta(days=61)),
        periods=96,
        freq="1H",
        inclusive="left",
    )
    coord_indices = coords_to_pd_index([GeoPosition(51.873419, 5.705929), GeoPosition(53.2194, 6.5665)])
    weather_factors = mock_factors
    data_dict = {
        weather_factor: (
            ["time", "coord"],
            np.zeros(shape=(len(timeline), len(coord_indices)), dtype=np.float64),
        )
        for weather_factor in weather_factors
    }
    ds = xr.Dataset(data_vars=data_dict, coords={"time": timeline, "coord": coord_indices})
    ds = ds.unstack("coord")
    return ds


@pytest.fixture(scope="session")
def mock_dataset_arome(mock_coordinates, mock_factors):
    """
        returns a mock Xarray Dataset for
    Args:
        mock_coordinates:
        mock_factors:

    Returns:

    """
    timeline = pd.date_range(
        end=(datetime.utcnow() - relativedelta(days=6)),
        periods=96,
        freq="1H",
        inclusive="left",
    )
    coord_indices = coords_to_pd_index([GeoPosition(51.873419, 5.705929), GeoPosition(53.2194, 6.5665)])
    weather_factors = mock_factors
    data_dict = {
        weather_factor: (
            ["prediction_moment", "time", "coord"],
            np.zeros(shape=(48, len(timeline), len(coord_indices)), dtype=np.float64),
        )
        for weather_factor in weather_factors
    }

    ds = xr.Dataset(
        data_vars=data_dict,
        coords={
            "prediction_moment": timeline[0:48],
            "time": timeline,
            "coord": coord_indices,
        },
    )
    ds = ds.unstack("coord")
    return ds
