#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

# repo_get_repository_location() isn't tested as it only fetches a value and if none is found a specific value is used.
# A test would therefore be bigger and more error-prone than the code itself.
import glob
import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import PropertyMock, patch

import pytest
from loguru import logger

from weather_provider_api.core.initializers.logging_handler import initialize_logging
from weather_provider_api.routers.weather.sources.knmi.client.arome_repository import (
    HarmonieAromeRepository,
)
from weather_provider_api.routers.weather.utils.date_helpers import subtract_months


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
                from_date=existing_dates['from'], to_date=subtract_months(existing_dates['to'], months=1)
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
