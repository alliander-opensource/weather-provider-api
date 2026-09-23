# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.pandas_helpers import coords_to_pd_index


@pytest.fixture(scope="session")
def _get_mock_repository_dir() -> Path:
    return Path(tempfile.gettempdir()).joinpath("PyTest_REPO")


@pytest.fixture(scope="session")
def mock_coordinates() -> list[tuple[float, float]]:
    return [(51.873419, 5.705929), (53.2194, 6.5665)]


@pytest.fixture(scope="session")
def mock_factors() -> list[str]:
    return [
        "fake_factor_1",
        "fake_factor_2",
        "fake_factor_3",
        "fake_factor_4",
        "fake_factor_5",
    ]


@pytest.fixture(scope="session")
def mock_dataset(mock_coordinates, mock_factors):
    """Generate a mock dataset for testing purposes."""
    timeline = pd.date_range(end=datetime.now(tz=None), periods=96, freq="1h", inclusive="left")
    coord_indices = coords_to_pd_index([GeoPosition(51.873419, 5.705929), GeoPosition(53.2194, 6.5665)])
    weather_factors = mock_factors
    data_dict = {
        weather_factor: (
            ["time", "coord"],
            np.zeros(shape=(len(timeline), len(coord_indices)), dtype=np.float64),
        )
        for weather_factor in weather_factors
    }
    mindex_coords = xr.Coordinates.from_pandas_multiindex(coord_indices, "coord")
    ds = xr.Dataset(data_vars=data_dict, coords={"time": timeline, **mindex_coords})
    ds = ds.unstack("coord")
    return ds


@pytest.fixture(scope="session")
def mock_dataset_era5(mock_coordinates, mock_factors):
    """Generate a mock ERA5 dataset for testing."""
    timeline = pd.date_range(
        end=(datetime.now(tz=UTC) - timedelta(days=61)),
        periods=96,
        freq="1h",
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
    mindex_coords = xr.Coordinates.from_pandas_multiindex(coord_indices, "coord")
    ds = xr.Dataset(data_vars=data_dict, coords={"time": timeline, **mindex_coords})
    ds = ds.unstack("coord")
    return ds


@pytest.fixture(scope="session")
def mock_dataset_arome(mock_coordinates, mock_factors):
    """Generate an AROME mock dataset for testing."""
    timeline = pd.date_range(
        end=(datetime.now(tz=UTC) - timedelta(days=6)),
        periods=96,
        freq="1h",
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

    # Explicitly convert MultiIndex to xarray coordinates to avoid FutureWarning
    mindex_coords = xr.Coordinates.from_pandas_multiindex(coord_indices, "coord")
    ds = xr.Dataset(
        data_vars=data_dict,
        coords={
            "prediction_moment": timeline[0:48],
            "time": timeline,
            **mindex_coords,
        },
    )
    ds = ds.unstack("coord")
    return ds
