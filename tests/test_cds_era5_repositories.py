# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from weather_provider_api.routers.weather.base_models.repository import RepoDataFetchResult, RepoUpdateResult
from weather_provider_api.routers.weather.sources.cds.client.era5land_repository import ERA5LandRepository
from weather_provider_api.routers.weather.sources.cds.client.era5sl_repository import ERA5SLRepository


@pytest.fixture(params=[ERA5LandRepository, ERA5SLRepository], ids=["era5land", "era5sl"])
def repository(
    request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> ERA5LandRepository | ERA5SLRepository:
    """Create either ERA5 repository with isolated temporary storage."""
    repository_class = request.param
    monkeypatch.setattr(repository_class, "storage_path", property(lambda self: tmp_path))
    return repository_class()


def test_date_availability_covers_ten_year_window(
    repository: ERA5LandRepository | ERA5SLRepository,
) -> None:
    """Test that both repositories expose the expected five-day lag and ten-year range."""
    today = datetime.now(UTC).date()

    assert repository.newest_date_available == today - timedelta(days=5)
    assert repository.oldest_date_available < repository.newest_date_available
    assert repository.oldest_date_available.year in {today.year - 10, today.year - 11}


def test_file_selection_and_cleanup_use_repository_prefix(
    repository: ERA5LandRepository | ERA5SLRepository,
) -> None:
    """Test selecting in-range monthly files and removing out-of-range files."""
    prefix = f"cds_{repository.source_and_model['model']}_"
    current_month = repository.newest_date_available.replace(day=1)
    current_file = repository.absolute_storage_path / f"{prefix}{current_month:%Y-%m}.nc"
    old_file = repository.absolute_storage_path / f"{prefix}2000-01.nc"
    invalid_file = repository.absolute_storage_path / f"{prefix}invalid.nc"
    current_file.touch()
    old_file.touch()
    invalid_file.touch()

    selected = repository._retrieve_files_matching_period(  # type: ignore[reportPrivateUsage]
        current_month, repository.newest_date_available
    )

    assert selected == [current_file]
    repository.cleanup_storage()
    assert current_file.exists()
    assert not old_file.exists()
    assert invalid_file.exists()


def test_filter_dataset_by_locations_and_factors(
    repository: ERA5LandRepository | ERA5SLRepository,
) -> None:
    """Test nearest-location selection and ignoring unavailable factors."""
    dataset = xr.Dataset(
        {
            "temperature": (("time", "lat", "lon"), np.ones((1, 2, 2))),
            "humidity": (("time", "lat", "lon"), np.zeros((1, 2, 2))),
        },
        coords={"time": [datetime(2026, 9, 22)], "lat": [51.8, 52.0], "lon": [5.7, 5.9]},
    )

    filtered = repository._filter_dataset_by_locations_and_factors(  # type: ignore[reportPrivateUsage]
        dataset, locations=[(51.87, 5.71)], factors=["temperature", "not_available"]
    )

    assert list(filtered.data_vars) == ["temperature"]
    assert filtered.lat.values.tolist() == [51.8]
    assert filtered.lon.values.tolist() == [5.7]


def test_retrieve_data_returns_empty_success_for_no_matching_files(
    repository: ERA5LandRepository | ERA5SLRepository,
) -> None:
    """Test the no-file retrieval result without reading external data."""
    result, status = repository.retrieve_data(
        from_date=date(2000, 1, 1),
        to_date=date(2000, 1, 31),
        locations=[(52.0, 5.0)],
        factors=["temperature"],
    )

    assert result is None
    assert status == RepoDataFetchResult.SUCCESS


def test_update_stops_when_cleanup_fails(
    repository: ERA5LandRepository | ERA5SLRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that update does not start a download after cleanup failure."""
    monkeypatch.setattr(type(repository), "cleanup_storage", lambda self: RepoUpdateResult.FAILURE) # type: ignore

    result, message = repository.update()

    assert result == RepoUpdateResult.FAILURE
    assert "Failed to clean up" in message