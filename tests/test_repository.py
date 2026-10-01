# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import date
from pathlib import Path

import numpy as np
import pytest
import xarray as xr

import weather_provider_api.routers.weather.base_models.repository as repository_module
from weather_provider_api.routers.weather.base_models.repository import (
    RepoDataFetchResult,
    RepoUpdateResult,
    WeatherRepositoryBase,
    WeatherRepositoryConfiguration,
)


class ConcreteRepository(WeatherRepositoryBase):
    """Concrete repository implementation for testing shared behavior."""

    @property
    def oldest_date_available(self) -> date:
        return date(2026, 1, 1)

    @property
    def newest_date_available(self) -> date:
        return date(2026, 12, 31)

    def update(self, *, run_in_testmode: bool = False) -> tuple[RepoUpdateResult, str]:
        return RepoUpdateResult.SUCCESS, "updated"

    def cleanup_storage(self) -> RepoUpdateResult:
        return RepoUpdateResult.SUCCESS

    def retrieve_data(
        self, from_date: date, to_date: date, locations: list[tuple[float, float]], factors: list[str]
    ) -> tuple[xr.Dataset | None, RepoDataFetchResult]:
        return None, RepoDataFetchResult.NO_DATA_AVAILABLE


@pytest.fixture
def repository(tmp_path: Path) -> ConcreteRepository:
    """Create a concrete repository in temporary storage."""
    return ConcreteRepository(
        WeatherRepositoryConfiguration(
            identifier="Test repository",
            storage_path=tmp_path / "repository",
            storage_states={"custom"},
            temporal_file_identifier="%Y%m%d",
            affiliated_source_and_model=("test", "model"),
        )
    )


def test_configuration_properties_and_metadata(repository: ConcreteRepository) -> None:
    """Test shared configuration properties and metadata rendering."""
    assert repository.identifier == "Test repository"
    assert repository.source_and_model == {"source": "test", "model": "model"}
    assert repository.storage_path.exists()
    assert {"custom", "raw", "processed"}.issubset(repository.config.storage_states)
    assert "Test repository" in repository.metadata
    assert "test (( model ))" in repository.metadata


def test_extract_datetime_tag_and_retrieve_files_by_period(repository: ConcreteRepository) -> None:
    """Test date-tag extraction and filtering of repository NetCDF files."""
    matching_file = repository.storage_path / "test_model_20260922.nc"
    outside_file = repository.storage_path / "test_model_20250101.nc"
    invalid_file = repository.storage_path / "test_model_invalid.nc"
    matching_file.touch()
    outside_file.touch()
    invalid_file.touch()

    assert repository._extract_datetime_tag_from_file_name(matching_file.name) == "20260922"  # type: ignore[reportPrivateUsage]
    assert repository._extract_datetime_tag_from_file_name(invalid_file.name) is None  # type: ignore[reportPrivateUsage]
    assert repository._retrieve_files_matching_period(  # type: ignore[reportPrivateUsage]
        date(2026, 9, 1), date(2026, 9, 30)
    ) == [matching_file]


def test_filter_dataset_selects_factors_and_nearest_locations() -> None:
    """Test shared dataset filtering for one and multiple requested locations."""
    dataset = xr.Dataset(
        {
            "temperature": (("latitude", "longitude"), np.ones((2, 2))),
            "humidity": (("latitude", "longitude"), np.zeros((2, 2))),
        },
        coords={"latitude": [51.8, 52.0], "longitude": [5.7, 5.9]},
    )

    filtered = ConcreteRepository._filter_dataset(  # type: ignore[reportPrivateUsage]
        dataset, locations=[(51.81, 5.71), (51.99, 5.89)], factors=["temperature"]
    )

    assert list(filtered.data_vars) == ["temperature"]
    assert filtered.sizes["location"] == 2

    assert ConcreteRepository._filter_dataset(dataset, locations=[], factors=["temperature"]).equals(xr.Dataset())  # type: ignore[reportPrivateUsage]


def test_safely_delete_file_handles_existing_and_missing_paths(tmp_path: Path) -> None:
    """Test safe deletion for files and non-files."""
    existing_file = tmp_path / "existing.txt"
    existing_file.touch()
    missing_file = tmp_path / "missing.txt"

    assert WeatherRepositoryBase.safely_delete_file(existing_file) is True
    assert not existing_file.exists()
    assert WeatherRepositoryBase.safely_delete_file(missing_file) is False
    assert WeatherRepositoryBase.safely_delete_file(tmp_path) is False


def test_purge_repository_requires_matching_identifier(repository: ConcreteRepository) -> None:
    """Test purge protection and idempotent purging of an absent repository."""
    assert repository.purge_repository("wrong identifier") == RepoUpdateResult.FAILURE
    assert repository.storage_path.exists()

    assert repository.purge_repository(repository.identifier) == RepoUpdateResult.SUCCESS
    assert not repository.storage_path.exists()
    assert repository.purge_repository(repository.identifier) == RepoUpdateResult.SUCCESS


def test_purge_repository_removes_relative_storage_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Purge removes a repository configured with a path relative to the storage root."""
    monkeypatch.setattr(repository_module, "APP_STORAGE_FOLDER", tmp_path)
    relative_repository = ConcreteRepository(
        WeatherRepositoryConfiguration(
            identifier="Relative test repository",
            storage_path=Path("relative-repository"),
            affiliated_source_and_model=("test", "model"),
        )
    )
    marker = relative_repository.absolute_storage_path / "marker.txt"
    marker.touch()

    assert relative_repository.purge_repository(relative_repository.identifier) == RepoUpdateResult.SUCCESS
    assert not relative_repository.absolute_storage_path.exists()