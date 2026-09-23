# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# repo_get_repository_location() isn't tested as it only fetches a value and if none is found a specific value is used.
# A test would therefore be bigger and more error-prone than the code itself.
import glob
import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import PropertyMock, patch

import numpy as np
import pytest
import xarray as xr
from loguru import logger

from weather_provider_api.core.initializers.logging_handler import initialize_logging
from weather_provider_api.routers.weather.base_models.repository import RepoUpdateResult
from weather_provider_api.routers.weather.sources.knmi.client.arome_repository import (
    AromeSuggestedFileHandling,
    HarmonieAromeRepository,
)
from weather_provider_api.routers.weather.utils.date_helpers import subtract_months


@pytest.fixture(autouse=True)
def _mock_knmi_data_platform_downloader(monkeypatch: pytest.MonkeyPatch):
    """Prevent the KNMI Data Platform Downloader from requiring an API key or network access.

    HarmonieAromeRepository instantiates a KNMIDataPlatformDownloader on construction, which normally
    requires a valid API key and performs a live validation request. For these repository tests we stub
    its initializer so no key or network connection is needed.
    """
    monkeypatch.setenv("KNMI_DATA_PLATFORM_KEY", "dummy-access-key")
    monkeypatch.setattr(
        "weather_provider_api.routers.weather.sources.knmi.client.arome_repository."
        "KNMIDataPlatFormDownloadClient.__init__",
        lambda self: None,
    )


def _get_mock_prefix(dummy_date: date):
    arome_repo = HarmonieAromeRepository()
    file_prefix = (
        f"{arome_repo.config.affiliated_source_and_model[0]}_{arome_repo.config.affiliated_source_and_model[1]}"
    )
    return (
        file_prefix
        + "_"
        + str(dummy_date.year)
        + str(dummy_date.month).zfill(2)
        + str(dummy_date.day).zfill(2)
        + "00.nc"
    )


def _fill_mock_repository(_get_mock_repository_dir: Path):  # type: ignore
    # Creating empty dummy files (one of each base type of file in the repository)
    mock_file_dates = {
        "from": subtract_months(datetime.now(UTC).date(), months=4),
        "to": subtract_months(datetime.now(UTC).date(), months=1),
    }

    for file_date in mock_file_dates.values():
        mock_file = Path(_get_mock_repository_dir).joinpath(_get_mock_prefix(file_date))
        open(mock_file.with_suffix(".nc"), "a", encoding="utf-8").close()
        logger.exception(f"Created mock file: {mock_file.with_suffix('.nc')}")
    return mock_file_dates


def test_arome_repository_cleanup(_get_mock_repository_dir: Path):
    """Test the cleanup function of the HarmonieAromeRepository."""
    with patch.object(HarmonieAromeRepository, "storage_path", new_callable=PropertyMock) as mock_path:
        mock_path.return_value = _get_mock_repository_dir
        arome_repo = HarmonieAromeRepository()

        # CLEANUP TEST 1:   The entire repository directory doesn't exist.
        # Expected result:  Cleanup does not create a new directory, and simply finishes without doing anything.
        if arome_repo.storage_path.exists():
            shutil.rmtree(arome_repo.storage_path)

        arome_repo.cleanup_storage()

        assert not Path(_get_mock_repository_dir).exists()

        # CLEANUP TEST 2:   A repository file within the active repository time-scope exists
        # Expected result:  Nothing should change
        regular_file = Path(
            _get_mock_repository_dir / (_get_mock_prefix(datetime.now(UTC) - timedelta(days=5)))
        ).with_suffix(".nc")
        open(regular_file, "a", encoding="utf-8").close()
        arome_repo.cleanup_storage()

        assert Path(regular_file).exists()

        # CLEANUP TEST 3:   A repository file outside the active repository time-scope exists
        # Expected result:  The outdated file has been removed, while the active file remains
        outside_scope_file = Path(
            _get_mock_repository_dir / _get_mock_prefix(datetime(2010, 1, 1, 0, 0, 0))
        ).with_suffix(".nc")
        open(outside_scope_file, "a", encoding="utf-8").close()
        arome_repo.cleanup_storage()

        assert not Path(outside_scope_file).exists()
        assert Path(regular_file).exists()

        # TEST 4: A "FORMATTED" repository file exists due to an unforeseen error in the repository
        #         The file should be removed, any current files matching the prefix should remain
        regular_formatted_file = Path(
            str(Path(_get_mock_repository_dir / _get_mock_prefix(datetime.now(UTC)))) + "_FORMATTED"
        ).with_suffix(".nc")
        open(outside_scope_file, "a", encoding="utf-8").close()
        arome_repo.cleanup_storage()

        assert not Path(regular_formatted_file).exists()
        assert Path(regular_file).exists()


def test_repo_get_month_filename(_get_mock_repository_dir: Path):
    """Test the _get_file_list_for_period function of the HarmonieAromeRepository."""
    with patch.object(HarmonieAromeRepository, "storage_path", new_callable=PropertyMock) as mock_path:
        mock_path.return_value = _get_mock_repository_dir
        arome_repo = HarmonieAromeRepository()

        # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
        if arome_repo.storage_path.exists():
            shutil.rmtree(arome_repo.storage_path)
        arome_repo.cleanup_storage()
        existing_dates = _fill_mock_repository(arome_repo.storage_path)
        assert len(glob.glob(str(arome_repo.storage_path.joinpath("knmi_arome")) + "*.*")) == 2  # Confirm file creation

        # FETCHING TEST 1:  One period outside the scope of the existing files
        result = [
            Path(file_name)
            for file_name in arome_repo._retrieve_files_matching_period(  # type: ignore
                from_date=existing_dates["from"], to_date=subtract_months(existing_dates["to"], months=1)
            )
        ]
        assert len(result) == 1
        assert result[0] == Path(
            f"{arome_repo.storage_path.joinpath('knmi_arome_')}{existing_dates['from'].strftime('%Y%m%d%H')}.nc"
        )


def test_arome_repository_remove_file(_get_mock_repository_dir: Path, caplog: pytest.LogCaptureFixture):
    """Test the _safely_delete_file function of the HarmonieAromeRepository."""
    # First we make sure the logging system is initialized, to properly capture log messages during the test
    initialize_logging()

    # We patch the storage_path property to point to our mock repository directory,
    # and then we set up the repository with dummy files for testing
    with patch.object(HarmonieAromeRepository, "storage_path", new_callable=PropertyMock) as mock_path:
        mock_path.return_value = _get_mock_repository_dir
        arome_repo = HarmonieAromeRepository()

        # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
        if arome_repo.storage_path.exists():
            shutil.rmtree(arome_repo.storage_path)
        arome_repo.cleanup_storage()
        _fill_mock_repository(arome_repo.storage_path)  # Add the dummy-files

        # FILE REMOVAL TEST 1:  Try to remove an existing file from the repo
        # Expected result:      File is removed from the repo
        files_in_folder = glob.glob(str(arome_repo.storage_path.joinpath("*.*")))
        existing_file = files_in_folder[0]
        assert arome_repo.safely_delete_file(Path(existing_file)) is True
        assert not Path(existing_file).exists()

        # FILE REMOVAL TEST 2:  Try to remove a non-existing file from the repo
        non_existing_file = arome_repo.storage_path.joinpath("DEF_DOESNT_EXIST.NOPE")
        result = arome_repo.safely_delete_file(non_existing_file)
        assert result is False


def test_filter_file_list_down_to_wanted_files() -> None:
    """Test filtering by filename date, supported hour, and available date range."""
    repository = HarmonieAromeRepository()
    current_date = datetime.now(UTC).date()
    prefix = "knmi_arome_"
    valid_file = f"{prefix}{current_date:%Y%m%d}00.nc"
    invalid_hour = f"{prefix}{current_date:%Y%m%d}03.nc"
    invalid_date = f"{prefix}{(current_date + timedelta(days=1)):%Y%m%d}00.nc"

    result = repository._filter_file_list_down_to_wanted_files(  # type: ignore[reportPrivateUsage]
        [
            {"filename": valid_file, "size": 1},
            {"filename": invalid_hour, "size": 1},
            {"filename": invalid_date, "size": 1},
            {"filename": "not-an-arome-file.nc", "size": 1},
        ]
    )

    assert result == [{"filename": valid_file, "size": 1}]
    assert repository._filter_file_list_down_to_wanted_files(None) is None  # type: ignore[reportPrivateUsage]


def test_determine_suggested_file_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the handling recommendation for new, processed, deprecated, and duplicate files."""
    repository = HarmonieAromeRepository()
    file = {"filename": "knmi_arome_2026092200.tar", "size": 1}
    downloader = repository.knmi_data_platform_downloader

    assert repository._determine_suggested_file_handling(file, []) == AromeSuggestedFileHandling.UPDATE  # type: ignore[reportPrivateUsage]
    assert (
        repository._determine_suggested_file_handling(file, [{"state": "unexpected", "path": Path("file")}])
        == AromeSuggestedFileHandling.UPDATE  # type: ignore[reportPrivateUsage]
    )
    assert (
        repository._determine_suggested_file_handling(
            file,
            [
                {"state": "processed", "path": Path("file")},
                {"state": "deprecated", "path": Path("file.deprecated")},
            ],
        )
        == AromeSuggestedFileHandling.LEAVE_AS_IS  # type: ignore[reportPrivateUsage]
    )

    monkeypatch.setattr(downloader, "retrieve_download_information_for_file", lambda **kwargs: ("url", None))
    assert (
        repository._determine_suggested_file_handling(file, [{"state": "processed", "path": Path("file")}])
        == AromeSuggestedFileHandling.LEAVE_AS_IS  # type: ignore[reportPrivateUsage]
    )
    assert (
        repository._determine_suggested_file_handling(file, [{"state": "deprecated", "path": Path("file")}])
        == AromeSuggestedFileHandling.UPDATE_DEPRECATED  # type: ignore[reportPrivateUsage]
    )

    monkeypatch.setattr(
        downloader,
        "retrieve_download_information_for_file",
        lambda **kwargs: ("url", "file has been deprecated"),
    )
    assert (
        repository._determine_suggested_file_handling(file, [{"state": "processed", "path": Path("file")}])
        == AromeSuggestedFileHandling.DEPRECATE  # type: ignore[reportPrivateUsage]
    )
    assert (
        repository._determine_suggested_file_handling(file, [{"state": "deprecated", "path": Path("file")}])
        == AromeSuggestedFileHandling.LEAVE_AS_IS  # type: ignore[reportPrivateUsage]
    )


def test_process_file_update_test_mode() -> None:
    """Test that test mode skips downloading and processing."""
    repository = HarmonieAromeRepository()

    result = repository._process_file_update(  # type: ignore[reportPrivateUsage]
        {"name": "knmi_arome_2026092200.tar", "filename": "knmi_arome_2026092200.tar", "size": 1},
        [],
        run_in_testmode=True,
    )

    assert result == RepoUpdateResult.SUCCESS


def test_filter_dataset_by_locations_and_factors() -> None:
    """Test selection of nearest locations and requested available factors."""
    dataset = xr.Dataset(
        {
            "temperature": (("time", "latitude", "longitude"), np.ones((1, 2, 2))),
            "humidity": (("time", "latitude", "longitude"), np.zeros((1, 2, 2))),
        },
        coords={"time": [datetime(2026, 9, 22)], "latitude": [51.8, 52.0], "longitude": [5.7, 5.9]},
    )

    result = HarmonieAromeRepository._filter_dataset_by_locations_and_factors(  # type: ignore[reportPrivateUsage]
        dataset,
        locations=[(51.87, 5.71)],
        factors=["temperature", "missing_factor"],
    )

    assert list(result.data_vars) == ["temperature"]
    assert result.latitude.values.tolist() == [51.8]
    assert result.longitude.values.tolist() == [5.7]


def test_update_returns_success_or_timeout_when_no_files_are_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test update results when the data platform has no files to process."""
    repository = HarmonieAromeRepository()
    monkeypatch.setattr(repository, "get_files_available_for_download", lambda: [])
    repository.knmi_data_platform_downloader.data_platform_quota_timeout = datetime.now(UTC) - timedelta(minutes=1)

    result, message = repository.update()
    assert result == RepoUpdateResult.SUCCESS
    assert "up to date" in message

    repository.knmi_data_platform_downloader.data_platform_quota_timeout = datetime.now(UTC) + timedelta(hours=1)
    result, message = repository.update()
    assert result == RepoUpdateResult.TIMEOUT
    assert "quota timeout" in message


def test_process_file_updates_fails_when_more_than_half_the_files_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stop processing when the failure ratio indicates a broken update run."""
    repository = HarmonieAromeRepository()
    monkeypatch.setattr(
        repository,
        "_process_file_update",
        lambda file, existing_files, run_in_testmode: RepoUpdateResult.FAILURE,
    )
    files = [{"filename": f"knmi_arome_2026092{index}00.tar", "size": 1} for index in range(3)]

    result, message = repository._process_file_updates(files, [], run_in_testmode=False)  # type: ignore[reportPrivateUsage]

    assert result == RepoUpdateResult.FAILURE
    assert "More than 50%" in message


@pytest.mark.parametrize(
    ("download_information", "downloaded_file", "expected_result"),
    [
        (None, None, RepoUpdateResult.FAILURE),
        (("https://example.test/arome.tar", None), None, RepoUpdateResult.FAILURE),
        (("https://example.test/arome.tar", None), Path("arome.tar"), RepoUpdateResult.SUCCESS),
    ],
)
def test_download_and_process_file_handles_download_outcomes(
    monkeypatch: pytest.MonkeyPatch,
    download_information: tuple[str, str | None] | None,
    downloaded_file: Path | None,
    expected_result: RepoUpdateResult,
) -> None:
    """Return failure for unavailable download steps and process successful downloads."""
    repository = HarmonieAromeRepository()
    downloader = repository.knmi_data_platform_downloader
    monkeypatch.setattr(downloader, "retrieve_download_information_for_file", lambda **kwargs: download_information)
    monkeypatch.setattr(downloader, "retrieve_file", lambda **kwargs: downloaded_file)
    process_calls: list[tuple[str, Path]] = []

    def process_downloaded_file(file_name: str, tar_file: Path) -> RepoUpdateResult:
        process_calls.append((file_name, tar_file))
        return RepoUpdateResult.SUCCESS

    monkeypatch.setattr(repository, "_process_downloaded_file", process_downloaded_file)

    result = repository._download_and_process_file(  # type: ignore[reportPrivateUsage]
        {"filename": "knmi_arome_2026092200.tar", "size": 1}
    )

    assert result == expected_result
    if downloaded_file:
        assert process_calls == [("knmi_arome_2026092200.tar", downloaded_file)]
    else:
        assert process_calls == []


def test_process_downloaded_file_returns_failure_for_invalid_filename() -> None:
    """Reject an archive whose filename does not contain a datetime tag."""
    repository = HarmonieAromeRepository()

    result = repository._process_downloaded_file("invalid.tar", Path("invalid.tar"))  # type: ignore[reportPrivateUsage]

    assert result == RepoUpdateResult.FAILURE


def test_process_downloaded_file_returns_failure_when_processing_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Convert processing exceptions into a repository failure result."""
    repository = HarmonieAromeRepository()
    monkeypatch.setattr(
        "weather_provider_api.routers.weather.sources.knmi.client.arome_repository."
        "process_knmi_arome_cy43_p1_tar_file_into_netcdf",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("conversion failed")),
    )

    result = repository._process_downloaded_file(  # type: ignore[reportPrivateUsage]
        "knmi_arome_2026092200.tar", Path("arome.tar")
    )

    assert result == RepoUpdateResult.FAILURE


def test_process_file_update_dispatches_to_deprecate_or_download(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dispatch the suggested handling action to the matching operation."""
    repository = HarmonieAromeRepository()
    file = {"filename": "knmi_arome_2026092200.tar", "size": 1}
    existing_files = [{"state": "processed", "path": Path("existing.nc")}]
    calls: list[str] = []

    monkeypatch.setattr(
        repository,
        "_determine_suggested_file_handling",
        lambda file, existing_files: AromeSuggestedFileHandling.DEPRECATE,
    )
    monkeypatch.setattr(repository, "_deprecate_processed_files", lambda files: calls.append("deprecate"))
    assert repository._process_file_update(file, existing_files, run_in_testmode=False) == RepoUpdateResult.SUCCESS  # type: ignore[reportPrivateUsage]

    monkeypatch.setattr(
        repository,
        "_determine_suggested_file_handling",
        lambda file, existing_files: AromeSuggestedFileHandling.UPDATE,
    )
    monkeypatch.setattr(repository, "_download_and_process_file", lambda file: calls.append("download") or RepoUpdateResult.SUCCESS)
    assert repository._process_file_update(file, existing_files, run_in_testmode=False) == RepoUpdateResult.SUCCESS  # type: ignore[reportPrivateUsage]

    assert calls == ["deprecate", "download"]


def test_get_existing_files_in_repository_classifies_and_skips_unknown_files(
    _get_mock_repository_dir: Path,
) -> None:
    """Classify supported repository suffixes and ignore invalid names."""
    with patch.object(HarmonieAromeRepository, "storage_path", new_callable=PropertyMock) as mock_path:
        mock_path.return_value = _get_mock_repository_dir
        repository = HarmonieAromeRepository()
        if repository.absolute_storage_path.exists():
            shutil.rmtree(repository.absolute_storage_path)
        repository.absolute_storage_path.mkdir(parents=True)
        repository.absolute_storage_path.joinpath("knmi_arome_2026092200.nc").touch()
        repository.absolute_storage_path.joinpath("knmi_arome_2026092200.raw.nc").touch()
        repository.absolute_storage_path.joinpath("knmi_arome_2026092200.deprecated.nc").touch()
        repository.absolute_storage_path.joinpath("not-an-arome-file.nc").touch()

        result = repository.get_existing_files_in_repository()

    assert {file["state"] for file in result} == {"processed", "raw", "deprecated"}
    assert len(result) == 3
