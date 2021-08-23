#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.

# repo_get_repository_location() isn't tested as it only fetches a value and if none is found a specific value is used.
# A test would therefore be bigger and more error prone than the code itself.
import glob
import os
import random
import secrets
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from dateutil.relativedelta import relativedelta

from app.routers.weather.sources.cds.client.era5sl_repository import ERA5SLRepository
from app.routers.weather.utils.geo_position import GeoPosition
from app.routers.weather.utils.pandas_helpers import coords_to_pd_index


def _get_mock_prefix(dummy_date: datetime):
    era5sl_repo = ERA5SLRepository()
    return era5sl_repo.file_prefix + '_' + str(dummy_date.replace(day=1).year) + "_" + \
           str(dummy_date.replace(day=1).month).zfill(2)


def _fill_mock_repository(_get_mock_repository_dir: Path):
    # Creating empty dummy files (one of each base type of file in the repository)
    mock_file_dates = [datetime.utcnow() + relativedelta(months=-1), datetime.utcnow() + relativedelta(months=-4)]

    for file_date in mock_file_dates:
        mock_file = Path(_get_mock_repository_dir).joinpath(_get_mock_prefix(file_date))
        open(mock_file.with_suffix('.nc'), 'a').close()
        open(Path(str(mock_file) + "_TEMP").with_suffix('.nc'), 'a').close()
        open(Path(str(mock_file) + "_UNFORMATTED").with_suffix('.nc'), 'a').close()
        open(Path(str(mock_file) + "_FORMATTED").with_suffix('.nc'), 'a').close()
        open(Path(str(mock_file) + "_INCOMPLETE").with_suffix('.nc'), 'a').close()

    return mock_file_dates


def _empty_folder(folder: Path):
    for file in glob.glob(str(folder) + '/*'):
        os.remove(file)


def test_era5sl_repository_cleanup(_get_mock_repository_dir: Path):
    era5sl_repo = ERA5SLRepository()
    era5sl_repo.repository_folder = _get_mock_repository_dir

    # CLEANUP TEST 1:   The entire repository directory doesn't exist.
    # Expected result:  An empty repository directory was made
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)

    era5sl_repo.cleanup()

    assert Path(_get_mock_repository_dir).exists()

    # CLEANUP TEST 2:   A repository file within the active repository time-scope exists
    # Expected result:  Nothing should change
    regular_file = Path(_get_mock_repository_dir / (_get_mock_prefix(datetime.utcnow()
                                                                     - relativedelta(days=5)))).with_suffix('.nc')
    open(regular_file, 'a').close()
    era5sl_repo.cleanup()

    assert Path(regular_file).exists()

    # CLEANUP TEST 3:   A repository file outside the active repository time-scope exists
    # Expected result:  The outdated file has been removed, while the active file remains
    outside_scope_file = Path(_get_mock_repository_dir /
                              _get_mock_prefix(datetime(2010, 1, 1, 0, 0, 0))).with_suffix('.nc')
    open(outside_scope_file, 'a').close()
    era5sl_repo.cleanup()

    assert not Path(outside_scope_file).exists()
    assert Path(regular_file).exists()

    # TEST 4: A "FORMATTED" repository file exists due to an unforeseen error in the repository
    #         The file should be removed, any current files matching the prefix should remain
    regular_formatted_file = Path(str(Path(_get_mock_repository_dir / _get_mock_prefix(datetime.utcnow())))
                                  + '_FORMATTED').with_suffix('.nc')
    open(outside_scope_file, 'a').close()
    era5sl_repo.cleanup()

    assert not Path(regular_formatted_file).exists()
    assert Path(regular_file).exists()


def test_repository_should_file_update(_get_mock_repository_dir: Path):
    era5sl_repo = ERA5SLRepository()
    era5sl_repo.repository_folder = _get_mock_repository_dir

    # Make sure the mock repo-folder exists, and is completely empty
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()  # The repo cleanup() function re-creates the folder

    # Create a prefix for a usable dummy file
    mock_file = era5sl_repo.repository_folder.joinpath(_get_mock_prefix(datetime.utcnow() + relativedelta(months=-1)))

    # Create a permanent file from the prefix
    open(str(mock_file.with_suffix('.nc')), 'a').close()

    # UPDATE TEST 1:    The file to check is a permanent file
    # Expected result:  The response should indicate that no update is required
    assert not era5sl_repo._file_requires_update(str(mock_file))

    # UPDATE TEST 2:    The file to check is an incomplete file
    # Expected result:  The response should indicate that an update is required
    os.rename(mock_file.with_suffix('.nc'), Path(str(mock_file) + '_INCOMPLETE').with_suffix('.nc'))
    assert era5sl_repo._file_requires_update(str(mock_file))

    # UPDATE TEST 3:    The file to check is a temporary file, not old enough to be replaced yet by a permanent one
    # Expected result:  The response should indicate that no update is required
    os.rename(Path(str(mock_file) + '_INCOMPLETE').with_suffix('.nc'),
              Path(str(mock_file) + '_TEMP').with_suffix('.nc'))
    assert not era5sl_repo._file_requires_update(str(mock_file))

    # UPDATE TEST 4:    The file to check is a temporary file, and old enough to be replaced yet by a permanent one
    # Expected result:  The response should indicate that an update is required
    new_file_prefix = _get_mock_prefix(datetime.utcnow() +
                                       relativedelta(months=-(era5sl_repo.age_of_permanence_in_months + 1)))
    new_file_prefix = Path(era5sl_repo.repository_folder).joinpath(new_file_prefix)
    os.rename(Path(str(mock_file) + '_TEMP').with_suffix('.nc'),
              Path(str(new_file_prefix) + '_TEMP').with_suffix('.nc'))

    assert era5sl_repo._file_requires_update(str(mock_file))

    # UPDATE TEST 5:    The file to check is an unformatted file. Normally these shouldn't exist, but on the off-chance
    # Expected result:  The response should indicate that an update is required
    os.rename(Path(str(new_file_prefix) + '_TEMP').with_suffix('.nc'),
              Path(str(mock_file) + '_UNFORMATTED').with_suffix('.nc'))
    assert era5sl_repo._file_requires_update(str(mock_file))


def test_repo_get_month_filename(_get_mock_repository_dir: Path):
    era5sl_repo = ERA5SLRepository()
    era5sl_repo.repository_folder = _get_mock_repository_dir

    # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()
    existing_dates = _fill_mock_repository(era5sl_repo.repository_folder)
    assert len(glob.glob(str(era5sl_repo.repository_folder.joinpath('ERA5SL')) + '*.*')) == 10  # Confirm file creation

    # FETCHING TEST 1:  All file-types exist, direct period result request
    # Expected result:  Only the definitive file is returned, the rest is removed from the folder
    file_prefix = era5sl_repo.repository_folder.joinpath(_get_mock_prefix(existing_dates[0]))

    result = era5sl_repo._get_file_list_for_period(existing_dates[0], existing_dates[0])
    assert len(result) == 1
    assert result == [(str(file_prefix) + '.nc')]

    # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()
    existing_dates = _fill_mock_repository(era5sl_repo.repository_folder)
    assert len(glob.glob(str(era5sl_repo.repository_folder.joinpath('ERA5SL')) + '*.*')) == 10  # Confirm file creation

    # FETCHING TEST 2:  All types but the definitive file exist, direct period result request
    # Expected result:  Only the INCOMPLETE file is returned, the rest is removed from the folder
    os.remove(Path(str(file_prefix) + ".nc"))
    result = era5sl_repo._get_file_list_for_period(existing_dates[0], existing_dates[0])
    assert len(result) == 1
    assert result == [(str(file_prefix) + '_TEMP.nc')]

    # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()
    existing_dates = _fill_mock_repository(era5sl_repo.repository_folder)
    assert len(glob.glob(str(era5sl_repo.repository_folder.joinpath('ERA5SL')) + '*.*')) == 10  # Confirm file creation

    # FETCHING TEST 3:  All types but the definitive and temporary types exist, direct period result request
    # Expected result:  Only the INCOMPLETE file is returned, the rest is removed from the folder
    os.remove(Path(str(file_prefix) + ".nc"))
    os.remove(Path(str(file_prefix) + "_TEMP.nc"))
    result = era5sl_repo._get_file_list_for_period(existing_dates[0], existing_dates[0])
    assert len(result) == 1
    assert result == [(str(file_prefix) + '_INCOMPLETE.nc')]

    # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()
    existing_dates = _fill_mock_repository(era5sl_repo.repository_folder)
    assert len(glob.glob(str(era5sl_repo.repository_folder.joinpath('ERA5SL')) + '*.*')) == 10  # Confirm file creation

    # FETCHING TEST 4:  Only temporary file types exist
    # Expected result:  No valid files should be found, the temporary files should be removed from the folder
    os.remove(Path(str(file_prefix) + ".nc"))
    os.remove(Path(str(file_prefix) + "_TEMP.nc"))
    os.remove(Path(str(file_prefix) + "_INCOMPLETE.nc"))
    result = era5sl_repo._get_file_list_for_period(existing_dates[0], existing_dates[0])
    assert len(result) == 0


def test_finalize_formatted_file(_get_mock_repository_dir):
    era5sl_repo = ERA5SLRepository()
    era5sl_repo.repository_folder = _get_mock_repository_dir

    # SETUP: Create a clean mock repo-folder
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()
    mock_file_prefix = str(era5sl_repo.repository_folder.joinpath(era5sl_repo.file_prefix))

    # FINALIZATION TEST 1:  The supplied formatted file is old enough to be permanent
    # Expected result:      The file is renamed without a suffix (1 file exists, without a suffix)
    file_date = (datetime.utcnow() - relativedelta(months=(era5sl_repo.age_of_permanence_in_months + 2)))
    mock_file = mock_file_prefix + '_' + str(file_date.year) + '_' + str(file_date.month).zfill(2)
    open(str(Path(mock_file)) + '_FORMATTED.nc', 'a').close()
    era5sl_repo._finalize_formatted_file(mock_file)
    result = glob.glob(str(Path(mock_file)) + '*.*')
    assert len(result) == 1
    assert result == [mock_file + '.nc']

    # FINALIZATION TEST 2:  No formatted files exist
    # Expected result:      An FileNotFound error should be raised
    with pytest.raises(FileNotFoundError) as e:
        era5sl_repo._finalize_formatted_file(mock_file)
    assert str(e.value.args[0]) == f'A formatted file for [{mock_file}] was not found'

    # SETUP: Removing the permanent file and adding new the new setup
    Path(mock_file + '.nc').unlink()
    open(Path(str(mock_file) + '_UNFORMATTED').with_suffix('.nc'), 'a').close()
    open(Path(str(mock_file) + '_FORMATTED').with_suffix('.nc'), 'a').close()
    open(Path(str(mock_file) + '_TEMP').with_suffix('.nc'), 'a').close()
    open(Path(str(mock_file) + '_INCOMPLETE').with_suffix('.nc'), 'a').close()

    # FINALIZATION TEST 3:  Formatted and unformatted files exist next to temporary and incomplete files
    # Expected Results:     The unformatted file remains untouched, and the formatted file is renamed into a permanent
    #                       file. The other files should be deleted.
    era5sl_repo._finalize_formatted_file(mock_file)
    result = glob.glob(str(Path(mock_file)) + '*.*')
    assert len(result) == 2
    assert result.sort() == [mock_file + '.nc', mock_file + '_UNFORMATTED.nc'].sort()

    # SETUP: Create a clean mock repo-folder
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()
    file_date = (datetime.utcnow() - relativedelta(months=(era5sl_repo.age_of_permanence_in_months - 1)))
    mock_file = mock_file_prefix + '_' + str(file_date.year) + '_' + str(file_date.month).zfill(2)
    open(str(Path(mock_file)) + '_FORMATTED.nc', 'a').close()

    # FINALIZATION TEST 4:  A formatted file exists with a date within the range for temporary files
    # Expected result:      The file is renamed to a temporary file ("_TEMP.nc")
    era5sl_repo._finalize_formatted_file(mock_file)
    result = glob.glob(str(Path(mock_file)) + '*.*')
    assert len(result) == 1
    assert result == [mock_file + '_TEMP.nc']

    # SETUP: Create a clean mock repo-folder
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()
    file_date = (datetime.utcnow() - relativedelta(days=5))
    mock_file = mock_file_prefix + '_' + str(file_date.year) + '_' + str(file_date.month).zfill(2)
    open(str(Path(mock_file)) + '_FORMATTED.nc', 'a').close()

    # FINALIZATION TEST 5:  A formatted file exists for the currently incomplete month
    # Expected result:      The file is renamed to an incomplete file ("_INCOMPLETE.nc")
    era5sl_repo._finalize_formatted_file(mock_file)
    result = glob.glob(str(Path(mock_file)) + '*.*')
    assert len(result) == 1
    assert result == [mock_file + '_INCOMPLETE.nc']


def test_era5sl_repository_remove_file(_get_mock_repository_dir):
    era5sl_repo = ERA5SLRepository()
    era5sl_repo.repository_folder = _get_mock_repository_dir

    # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()
    _fill_mock_repository(era5sl_repo.repository_folder)  # Add the dummy-files

    # FILE REMOVAL TEST 1:  Try to remove an existing file from the repo
    # Expected result:      File is removed from the repo
    files_in_folder = glob.glob(str(era5sl_repo.repository_folder.joinpath("*.*")))
    existing_file = files_in_folder[0]
    assert era5sl_repo._safely_delete_file(existing_file)

    # FILE REMOVAL TEST 2:  Try to remove an non-existing file from the repo
    # Expected result:      A FileNotFound Error is raised
    non_existing_file = era5sl_repo.repository_folder.joinpath("DEF_DOESNT_EXIST.NOPE")
    with pytest.raises(OSError) as e:
        era5sl_repo._safely_delete_file(non_existing_file)
    assert str(e.value.args[0]) == f'Could not safely delete file: {non_existing_file}'


def test_era5sl_repository_update(monkeypatch, _get_mock_repository_dir, mock_coordinates):
    # Full test for the update system. Downloads are intercepted by corresponding mock functions.
    era5sl_repo = ERA5SLRepository()
    era5sl_repo.repository_folder = _get_mock_repository_dir

    # SETUP: Create a clean mock repo-folder with dummy-files for 2 dates
    if era5sl_repo.repository_folder.exists():
        shutil.rmtree(era5sl_repo.repository_folder)
    era5sl_repo.cleanup()
    months_in_full_update = (era5sl_repo.get_last_day_of_repo().year - era5sl_repo.get_first_day_of_repo().year) * 12 + \
                            (era5sl_repo.get_last_day_of_repo().month - era5sl_repo.get_first_day_of_repo().month) + 1

    # MOCKING: Intercepting the ERA5SL Download function and returning a dummy dataset for further handling
    def mock_download_era5sl_file(self, weather_factors, years, months, days, area_box, target_location):
        timeline = pd.date_range(end=datetime.utcnow(), periods=96, freq="1H", closed="left")
        coord_indices = coords_to_pd_index(
            [GeoPosition(coordinate[0], coordinate[1]) for coordinate in mock_coordinates])
        coord = coord_indices[0]

        data_dict = {
            weather_factor: (
                ["time", "longitude", "latitude"],
                np.zeros(shape=(len(timeline), 1, 1), dtype=np.float64),
            )
            for weather_factor in weather_factors
        }

        ds = xr.Dataset(data_vars=data_dict, coords={"time": timeline, "longitude": [coord[1]],
                                                     "latitude": [coord[0]]})
        ds.to_netcdf(path=target_location, format="NETCDF4", engine="netcdf4")

    monkeypatch.setattr(ERA5SLRepository, '_download_era5sl_file', mock_download_era5sl_file)

    # UPDATE TEST 1:    General update request with no pre-existing files
    # Expected result:  Repository files will be 'downloaded' and build for the entire repository period
    assert era5sl_repo.update()  # No errors expected
    files_in_repository = glob.glob(str(era5sl_repo.repository_folder.joinpath("*.*")))
    assert len(files_in_repository) == months_in_full_update  # Proper number of files

    # SETUP: Remove two random files
    random_number = secrets.randbelow(len(files_in_repository) - 1)
    era5sl_repo._safely_delete_file(files_in_repository[random_number])
    second_random_number = random_number
    while second_random_number == random_number:
        second_random_number = secrets.randbelow(len(files_in_repository) - 1)
    era5sl_repo._safely_delete_file(files_in_repository[second_random_number])

    # UPDATE TEST 2:    General update test with files both there and missing
    # Expected result:  Missing repository files will be 'downloaded' and build, and the rest will be skipped
    assert era5sl_repo.update()  # No errors expected
    files_in_repository = glob.glob(str(era5sl_repo.repository_folder.joinpath("*.*")))
    assert len(files_in_repository) == months_in_full_update  # Proper number of files

    # SETUP: Remove two random files
    random_number = secrets.randbelow(len(files_in_repository) - 1)
    era5sl_repo._safely_delete_file(files_in_repository[random_number])
    second_random_number = random_number
    while second_random_number == random_number:
        second_random_number = secrets.randbelow(len(files_in_repository) - 1)
    era5sl_repo._safely_delete_file(files_in_repository[second_random_number])

    # SETUP: Rename two random files
    files_in_repository = glob.glob(str(era5sl_repo.repository_folder.joinpath("*.*")))  # Refresh after delete
    random_number = secrets.randbelow(len(files_in_repository) - 1)
    file_to_rename = files_in_repository[random_number]
    second_random_number = random_number
    while second_random_number == random_number:
        second_random_number = secrets.randbelow(len(files_in_repository) -1)
    second_file_to_rename = files_in_repository[second_random_number]
    Path(files_in_repository[random_number]).rename(str(file_to_rename[:-3]) + '_UNFORMATTED.nc')
    Path(files_in_repository[second_random_number]).rename(str(second_file_to_rename[:-3]) + '_FORMATTED.nc')

    # UPDATE TEST 3:    General update test with files existing and missing, but also with (un)formatted files for both
    # Expected result:  The (un)formatted files are all deleted, and any missing repo files newly downloaded and build
    assert era5sl_repo.update()  # No errors expected
    files_in_repository = glob.glob(str(era5sl_repo.repository_folder.joinpath("*.*")))
    assert len(files_in_repository) == months_in_full_update  # Proper number of files
