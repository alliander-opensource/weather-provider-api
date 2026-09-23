# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from weather_provider_api.routers.weather.base_models.repository import (
    RepoDataFetchResult,
    RepoUpdateResult,
)
from weather_provider_api.routers.weather.sources.knmi.client.actuele_waarnemingen_register_repository import (
    ActueleWaarnemingenRegisterRepository,
)


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ActueleWaarnemingenRegisterRepository:
    """Create a register repository using a temporary storage directory."""
    monkeypatch.setattr(
        ActueleWaarnemingenRegisterRepository,
        "storage_path",
        property(lambda self: tmp_path),
    )
    return ActueleWaarnemingenRegisterRepository()


def _dataset(observation_time: datetime, temperature: float = 10.0) -> xr.Dataset:
    return xr.Dataset(
        {"temperature": (("time", "STN"), np.array([[temperature]]))},
        coords={"time": [observation_time], "STN": [8]},
    )


def test_update_file_creates_repository_file(
    repository: ActueleWaarnemingenRegisterRepository,
) -> None:
    """Test that new observations create a NetCDF repository file."""
    observation_time = datetime(2026, 9, 22, 10, 0)

    result = repository._update_file_with_new_data(  # type: ignore[reportPrivateUsage]
        _dataset(observation_time),
        datetime(2026, 9, 22, 10, 5, tzinfo=UTC),
    )

    assert result == RepoDataFetchResult.SUCCESS
    assert repository.storage_filename.exists()
    stored_dataset = xr.load_dataset(repository.storage_filename, engine="netcdf4")
    assert stored_dataset.temperature.values.tolist() == [[10.0]]


def test_update_file_skips_observation_within_five_minutes(
    repository: ActueleWaarnemingenRegisterRepository,
) -> None:
    """Test that observations less than five minutes apart are not duplicated."""
    observation_time = datetime(2026, 9, 22, 10, 0)
    repository._update_file_with_new_data(  # type: ignore[reportPrivateUsage]
        _dataset(observation_time),
        datetime(2026, 9, 22, 10, 0, tzinfo=UTC),
    )

    result = repository._update_file_with_new_data(  # type: ignore[reportPrivateUsage]
        _dataset(observation_time + timedelta(minutes=4), temperature=11.0),
        datetime(2026, 9, 22, 10, 4, tzinfo=UTC),
    )

    assert result == RepoDataFetchResult.NO_DATA_AVAILABLE
    stored_dataset = xr.load_dataset(repository.storage_filename, engine="netcdf4")
    assert stored_dataset.time.size == 1
    assert stored_dataset.temperature.values.tolist() == [[10.0]]


def test_update_file_merges_observation_after_five_minutes(
    repository: ActueleWaarnemingenRegisterRepository,
) -> None:
    """Test that sufficiently new observations are merged into the repository."""
    first_time = datetime(2026, 9, 22, 10, 0)
    repository._update_file_with_new_data(  # type: ignore[reportPrivateUsage]
        _dataset(first_time),
        datetime(2026, 9, 22, 10, 0, tzinfo=UTC),
    )

    result = repository._update_file_with_new_data(  # type: ignore[reportPrivateUsage]
        _dataset(first_time + timedelta(minutes=10), temperature=11.0),
        datetime(2026, 9, 22, 10, 10, tzinfo=UTC),
    )

    assert result == RepoDataFetchResult.SUCCESS
    stored_dataset = xr.load_dataset(repository.storage_filename, engine="netcdf4")
    assert stored_dataset.time.size == 2
    assert stored_dataset.temperature.values.flatten().tolist() == [10.0, 11.0]


def test_cleanup_storage_removes_observations_outside_scope(
    repository: ActueleWaarnemingenRegisterRepository,
) -> None:
    """Test that cleanup retains only observations from the active date range."""
    old_time = datetime.combine(repository.oldest_date_available - timedelta(days=1), datetime.min.time())
    current_time = datetime.combine(repository.newest_date_available, datetime.min.time())
    dataset = xr.concat([_dataset(old_time), _dataset(current_time, temperature=11.0)], dim="time")
    dataset.to_netcdf(repository.storage_filename, engine="netcdf4")

    result = repository.cleanup_storage()

    assert result == RepoUpdateResult.SUCCESS
    stored_dataset = xr.load_dataset(repository.storage_filename, engine="netcdf4")
    assert stored_dataset.time.size == 1
    assert pd.Timestamp(stored_dataset.time.values[0]).date() == repository.newest_date_available


def test_update_returns_failure_when_download_returns_no_dataset(
    repository: ActueleWaarnemingenRegisterRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that an unsuccessful observation download returns a failure result."""
    monkeypatch.setattr(
        "weather_provider_api.routers.weather.sources.knmi.client.actuele_waarnemingen_register_repository."
        "download_actuele_waarnemingen_weather",
        lambda: None,
    )

    result, message = repository.update()

    assert result == RepoUpdateResult.FAILURE
    assert "Failed to download" in message


def test_update_stores_downloaded_data_and_runs_cleanup(
    repository: ActueleWaarnemingenRegisterRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Store downloaded observations after cleaning the existing repository."""
    cleanup_calls: list[bool] = []
    monkeypatch.setattr(
        "weather_provider_api.routers.weather.sources.knmi.client.actuele_waarnemingen_register_repository."
        "download_actuele_waarnemingen_weather",
        lambda: _dataset(datetime(2026, 9, 22, 10, 0)),
    )
    monkeypatch.setattr(repository, "cleanup_storage", lambda: cleanup_calls.append(True) or RepoUpdateResult.SUCCESS)

    result, message = repository.update()

    assert result == RepoUpdateResult.SUCCESS
    assert "not implemented" in message
    assert cleanup_calls == [True]
    assert repository.storage_filename.exists()


def test_load_storage_dataset_deletes_corrupt_file(
    repository: ActueleWaarnemingenRegisterRepository,
) -> None:
    """Treat an unreadable storage file as absent after deleting it."""
    repository.storage_filename.write_bytes(b"not a netcdf file")

    result = repository._load_storage_dataset()  # type: ignore[reportPrivateUsage]

    assert result is None
    assert not repository.storage_filename.exists()


def test_latest_storage_time_handles_missing_and_numpy_timestamps() -> None:
    """Return UTC timestamps and None when a dataset lacks time data."""
    dataset = _dataset(datetime(2026, 9, 22, 10, 0))
    latest = ActueleWaarnemingenRegisterRepository._latest_storage_time(dataset)  # type: ignore[reportPrivateUsage]

    assert latest == datetime(2026, 9, 22, 10, 0, tzinfo=UTC)
    assert ActueleWaarnemingenRegisterRepository._latest_storage_time(xr.Dataset()) is None  # type: ignore[reportPrivateUsage]


def test_cleanup_storage_succeeds_when_repository_file_is_absent(
    repository: ActueleWaarnemingenRegisterRepository,
) -> None:
    """An absent registry has nothing to clean and is a successful cleanup."""
    assert repository.cleanup_storage() == RepoUpdateResult.SUCCESS


def test_cleanup_storage_deletes_corrupt_repository_file(
    repository: ActueleWaarnemingenRegisterRepository,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Delete a registry that cannot be loaded and report the failure."""
    repository.storage_filename.touch()
    monkeypatch.setattr(
        "weather_provider_api.routers.weather.sources.knmi.client.actuele_waarnemingen_register_repository."
        "xr.load_dataset",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("corrupt")),
    )

    result = repository.cleanup_storage()

    assert result == RepoUpdateResult.FAILURE
    assert not repository.storage_filename.exists()


def test_get_existing_files_reports_registry_file(repository: ActueleWaarnemingenRegisterRepository) -> None:
    """Report the single registry file when it exists."""
    repository.storage_filename.touch()

    result = repository.get_existing_files_in_repository()

    assert len(result) == 1
    assert result[0]["path"] == repository.storage_filename
    assert result[0]["state"] == "processed"