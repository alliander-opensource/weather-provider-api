#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.

# repo_get_repository_location() isn't tested as it only fetches a value and if none is found a specific value is used.
# A test would therefore be bigger and more error prone than the code itself.
import glob
import os
import shutil
from datetime import datetime
from pathlib import Path

import pytest
from dateutil.relativedelta import relativedelta

from weather_provider_api.app.routers.weather.sources.knmi.client.arome_repository import AromeRepository


def _get_mock_prefix(dummy_date: datetime):
    arome_repo = AromeRepository()
    return arome_repo.file_prefix + '_' + str(dummy_date.year) + str(dummy_date.month).zfill(2) + \
           str(dummy_date.day).zfill(2) + '_' + str(dummy_date.hour).zfill(2) + '00.nc'


def _fill_mock_repository(_get_mock_repository_dir: Path):
    # Creating empty dummy files (one of each base type of file in the repository)
    mock_file_dates = [datetime.utcnow() + relativedelta(months=-1), datetime.utcnow() + relativedelta(months=-4)]

    for file_date in mock_file_dates:
        mock_file = Path(_get_mock_repository_dir).joinpath(_get_mock_prefix(file_date))
        open(mock_file.with_suffix('.nc'), 'a').close()
    return mock_file_dates


def _empty_folder(folder: Path):
    for file in glob.glob(str(folder) + '/*'):
        os.remove(file)


def test_arome_repository_cleanup(_get_mock_repository_dir: Path):
    arome_repo = AromeRepository()
    arome_repo.repository_folder = _get_mock_repository_dir

    # CLEANUP TEST 1:   The entire repository directory doesn't exist.
    # Expected result:  An empty repository directory was made
    if arome_repo.repository_folder.exists():
        shutil.rmtree(arome_repo.repository_folder)

    arome_repo.cleanup()

    assert Path(_get_mock_repository_dir).exists()

    # CLEANUP TEST 2:   A repository file within the active repository time-scope exists
    # Expected result:  Nothing should change
    regular_file = Path(_get_mock_repository_dir / (_get_mock_prefix(datetime.utcnow()
                                                                     - relativedelta(days=5)))).with_suffix('.nc')
    print("REGULAR FILE == ", regular_file)
    open(regular_file, 'a').close()
    arome_repo.cleanup()

    assert Path(regular_file).exists()

    # CLEANUP TEST 3:   A repository file outside the active repository time-scope exists
    # Expected result:  The outdated file has been removed, while the active file remains
    outside_scope_file = Path(_get_mock_repository_dir /
                              _get_mock_prefix(datetime(2010, 1, 1, 0, 0, 0))).with_suffix('.nc')
    open(outside_scope_file, 'a').close()
    arome_repo.cleanup()

    assert not Path(outside_scope_file).exists()
    assert Path(regular_file).exists()

    # TEST 4: A "FORMATTED" repository file exists due to an unforeseen error in the repository
    #         The file should be removed, any current files matching the prefix should remain
    regular_formatted_file = Path(str(Path(_get_mock_repository_dir / _get_mock_prefix(datetime.utcnow())))
                                  + '_FORMATTED').with_suffix('.nc')
    open(outside_scope_file, 'a').close()
    arome_repo.cleanup()

    assert not Path(regular_formatted_file).exists()
    assert Path(regular_file).exists()


def test_repo_get_month_filename(_get_mock_repository_dir: Path):
    arome_repo = AromeRepository()
    arome_repo.repository_folder = _get_mock_repository_dir

    # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
    if arome_repo.repository_folder.exists():
        shutil.rmtree(arome_repo.repository_folder)
    arome_repo.cleanup()
    existing_dates = _fill_mock_repository(arome_repo.repository_folder)
    assert len(glob.glob(str(arome_repo.repository_folder.joinpath('AROME')) + '*.*')) == 2  # Confirm file creation

    # FETCHING TEST 1:  All file-types exist, direct period result request
    # Expected result:  Only the definitive file is returned, the rest is removed from the folder
    file_prefix = arome_repo.repository_folder.joinpath(_get_mock_prefix(existing_dates[0]))

    result = [Path(file_name) for file_name in
              arome_repo._get_file_list_for_period(existing_dates[1], existing_dates[0])]
    assert len(result) == 1
    assert result == [Path(str(file_prefix))]


def test_arome_repository_remove_file(_get_mock_repository_dir):
    arome_repo = AromeRepository()
    arome_repo.repository_folder = _get_mock_repository_dir

    # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
    if arome_repo.repository_folder.exists():
        shutil.rmtree(arome_repo.repository_folder)
    arome_repo.cleanup()
    _fill_mock_repository(arome_repo.repository_folder)  # Add the dummy-files

    # FILE REMOVAL TEST 1:  Try to remove an existing file from the repo
    # Expected result:      File is removed from the repo
    files_in_folder = glob.glob(str(arome_repo.repository_folder.joinpath("*.*")))
    existing_file = files_in_folder[0]
    assert arome_repo._safely_delete_file(existing_file)

    # FILE REMOVAL TEST 2:  Try to remove an non-existing file from the repo
    # Expected result:      A FileNotFound Error is raised
    non_existing_file = arome_repo.repository_folder.joinpath("DEF_DOESNT_EXIST.NOPE")
    with pytest.raises(OSError) as e:
        arome_repo._safely_delete_file(non_existing_file)
    assert str(e.value.args[0]) == f'Could not safely delete file: {non_existing_file}'


@pytest.mark.skip(reason="Still to be implemented")
def test_arome_repository_update(monkeypatch):
    # Full test for the update system. Downloads are intercepted by corresponding mock functions.
    # TODO: Implement
    pass