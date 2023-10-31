#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import glob
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Tuple

import xarray as xr
from dateutil.relativedelta import relativedelta
from loguru import logger

from weather_provider_api.routers.weather.repository.repository import RepositoryUpdateResult
from weather_provider_api.routers.weather.sources.cds.client import downloader

_FORMATTED_SUFFIX = ".FORMATTED.nc"
_UNFORMATTED_SUFFIX = ".UNFORMATTED.nc"
_INCOMPLETE_SUFFIX = ".INCOMPLETE.nc"
_TEMP_SUFFIX = ".TEMP.nc"


def _repository_callback(*args, **kwargs):  # pragma: no cover
    logger.info("Callback Received:")
    logger.info(" - Args: ", *args)
    logger.info(" - Kwargs: ", **kwargs)


def era5_update(
    file_prefix: str,
    repository_folder: str,
    repository_scope: Tuple[datetime, datetime],
    era5_dataset_name: str,
    era5_product_type: str,
    selected_factors: List[str],
    dataset_grid_resolution: Tuple[float, float],
    allowed_factors: Dict,
    maximum_allowed_runtime_in_minutes: int = (2 * 60),
    verify_last_available_date: bool = True,
):
    # Determine when to start and when to end
    start_of_update = datetime.utcnow()
    forced_end_of_update = start_of_update + relativedelta(minutes=maximum_allowed_runtime_in_minutes)

    # Set initial progress data
    current_months_processed = 0
    current_months_not_processable = 0
    average_time_per_month = 35  # Assuming 35 minutes processing time for the first item
    oldest_date_in_repo = repository_scope[0].date()
    newest_date_in_repo = repository_scope[1].date()

    logger.info(f"Started the update for repository [{file_prefix}]:")
    if verify_last_available_date:
        logger.info(f"Determining the most recent date available for [{era5_dataset_name}],[{era5_product_type}]")
        newest_date_in_repo = _get_actual_most_recent_data_for_model(
            newest_date_in_repo, era5_dataset_name, era5_product_type, dataset_grid_resolution
        )

    current_month_to_process = newest_date_in_repo.replace(day=1)
    while current_month_to_process >= oldest_date_in_repo.replace(day=1):
        if current_months_processed != 0 and current_months_processed > current_months_not_processable:
            average_time_per_month = (datetime.utcnow() - start_of_update).total_seconds() / current_months_processed

        if datetime.utcnow() + relativedelta(seconds=average_time_per_month) > forced_end_of_update:
            logger.info("There was not enough time left to process another file. Finishing up..")
            return RepositoryUpdateResult.timed_out

        try:
            process_month(
                file_prefix,
                repository_folder,
                current_month_to_process,
                era5_dataset_name,
                era5_product_type,
                dataset_grid_resolution,
                selected_factors,
                newest_date_in_repo,
                allowed_factors,
            )
        except Exception as e:
            logger.warning(
                f"Could not process month [{current_month_to_process.year}, {current_month_to_process.month}]: {e}"
            )
            current_months_not_processable += 1

        current_months_processed += 1
        current_month_to_process -= relativedelta(months=1)

    if current_months_processed > 1 and current_months_not_processable / current_months_processed > 0.3:
        # if over 30% of all requested months did not work and more than a month was requested return a failure value
        logger.error(
            "The margin of months that could not be processed exceeded set margins. Please contact an administrator."
        )
        return RepositoryUpdateResult.failure

    return RepositoryUpdateResult.completed


def process_month(
    file_name_prefix: str,
    repository_folder: str,
    month_to_process: date,
    dataset_name: str,
    product_name: str,
    grid_resolution: Tuple[float, float],
    factors: List[str],
    most_recent_data_date: date,
    allowed_factors: Dict,
):
    file_name = f"{file_name_prefix}_{month_to_process.year}_{str(month_to_process.month).zfill(2)}"
    file_path = Path(repository_folder).joinpath(file_name)

    if file_requires_update(file_path, month_to_process, most_recent_data_date):
        logger.debug(f"File update required for [{month_to_process.year}, {month_to_process.month}]")
        download_file = file_path.with_suffix(_UNFORMATTED_SUFFIX)
        download_era5_file(
            dataset=dataset_name,
            product_type=product_name,
            grid_resolution=grid_resolution,
            weather_factors=factors,
            years=[month_to_process.year],
            months=[month_to_process.month],
            days=list(range(1, 32)),
            target_location=download_file,
        )

        format_downloaded_file(download_file, allowed_factors)
        download_file.rename(file_path.with_suffix(_FORMATTED_SUFFIX))
        finalize_formatted_file(file_path, month_to_process, most_recent_data_date)


def file_requires_update(file_path: Path, current_month: date, verification_date: date):
    if file_path.with_suffix(".nc").exists():
        # A regular file exists, no updates required
        logger.debug("A regular file already exists: NO UPDATE REQUIRED")
        return False

    if file_path.with_suffix(_TEMP_SUFFIX).exists():
        # If a file is temporary we only check for a permanent update if more than 3 months have past since the current
        # most recent date with data.
        threshold_date = (verification_date - relativedelta(months=3)).replace(day=1)
        if current_month < threshold_date:
            logger.debug("A temporary file exists within the update range: UPDATE REQUIRED")
            return True
        logger.debug("A temporary file exists within the update range: UPDATE REQUIRED")
        return False

    # A file exists but isn't any regular supported type to be updated
    if file_path.with_suffix(_UNFORMATTED_SUFFIX).exists() or file_path.with_suffix(_FORMATTED_SUFFIX).exists():
        logger.debug("An unformatted file or formatted file exists: UPDATE REQUIRED")
        return True  # An update should both clean the UNFORMATTED file and generate a proper one

    if not file_path.with_suffix(".nc").exists() or file_path.with_suffix(_INCOMPLETE_SUFFIX).exists():
        logger.debug("No file exists, or it is still incomplete: UPDATE REQUIRED ")
        return True  # No file matching the mask or incomplete files always mean the update is required!

    files_in_folder = glob.glob(f"{file_path}*.nc")
    logger.warning(f"Unexpected files existed in the repository folder: {files_in_folder}. These should be dealt with.")
    return False


def format_downloaded_file(unformatted_file: Path, allowed_factors: Dict):
    logger.info(f"Formatting the downloaded file at: {unformatted_file}")
    ds_unformatted = load_file(unformatted_file)
    ds_unformatted.attrs = {}  # Remove unneeded attributes

    if "expver" in ds_unformatted.indexes.keys():
        # We remove the expver index used to denominate temporary data (5) and regular data (1) and add a field for it
        # NOTE: We removed the drop_sel version as it didn't quite have the same result as drop yet. Reverting until
        #  the proper use has been validated...
        ds_unformatted_expver5 = ds_unformatted.sel(expver=5).drop("expver").dropna("time", how="all")
        ds_unformatted_expver1 = ds_unformatted.sel(expver=1).drop("expver").dropna("time", how="all")

        # Recombine the data
        ds_unformatted = ds_unformatted_expver1.merge(ds_unformatted_expver5)
        ds_unformatted["is_permanent_data"] = False
    else:
        ds_unformatted["is_permanent_data"] = True

    # Rename the factors to their longer names:
    for factor in ds_unformatted.variables.keys():
        if factor in allowed_factors:
            ds_unformatted = ds_unformatted.rename_vars({factor: allowed_factors[factor]})

    # Rename and encode data where needed:
    ds_unformatted.time.encoding["units"] = "hours since 2016-01-01"
    ds_unformatted = ds_unformatted.rename(name_dict={"latitude": "lat", "longitude": "lon"})

    # Store the data
    ds_unformatted.to_netcdf(path=unformatted_file, format="NETCDF4", engine="netcdf4")


def finalize_formatted_file(file_path: Path, current_month: date, verification_date: date):
    logger.info(f"Finalizing the formatted file for location: {file_path}")
    formatted_file = file_path.with_suffix(_FORMATTED_SUFFIX)
    incomplete_month = verification_date.replace(day=1)
    permanent_month = (verification_date - relativedelta(months=3)).replace(day=1)

    if not formatted_file.exists():
        logger.error(f"Unexpected error: Expected file [{formatted_file}] did not exist!")
        raise FileNotFoundError(f"The pre-formatted month file [{formatted_file}] was not found!")

    # Cleanup old files:
    for file_suffix in [_TEMP_SUFFIX, _INCOMPLETE_SUFFIX]:
        if file_path.with_suffix(file_suffix).exists():
            _safely_delete_file(file_path.with_suffix(file_suffix))

    # Rename the file to its proper name:
    if current_month == verification_date.replace(day=1):
        # Current month means an incomplete file
        file_path.with_suffix(_FORMATTED_SUFFIX).rename(file_path.with_suffix(_INCOMPLETE_SUFFIX))
        logger.debug(f"Month [{current_month}] was renamed to: {file_path.with_suffix(_INCOMPLETE_SUFFIX)}")
    elif permanent_month < current_month < incomplete_month:
        # Non-permanent file
        file_path.with_suffix(_FORMATTED_SUFFIX).rename(file_path.with_suffix(_TEMP_SUFFIX))
        logger.debug(f"Month [{current_month}] was renamed to: {file_path.with_suffix(_TEMP_SUFFIX)}")
    else:
        # Permanent file
        file_path.with_suffix(_FORMATTED_SUFFIX).rename(file_path.with_suffix(".nc"))
        logger.debug(f'Month [{current_month}] was renamed to: {file_path.with_suffix(".nc")}')


def _get_actual_most_recent_data_for_model(
    date_to_start_from: date, era5_dataset_name: str, era5_product_type: str, grid_resolution: Tuple[float, float]
):
    got_proper_response = False
    date_to_check = date_to_start_from
    while not got_proper_response:
        try:
            download_era5_file(
                dataset=era5_dataset_name,
                product_type=era5_product_type,
                grid_resolution=grid_resolution,
                weather_factors=[
                    "stl1",
                ],  # Only one factor that exists in both datasets
                years=[date_to_check.year],
                months=[date_to_check.month],
                days=[date_to_check.day],
                target_location=tempfile.NamedTemporaryFile().name,
            )
            got_proper_response = True
        finally:
            if date_to_check < date_to_start_from - relativedelta(years=1):
                raise IOError("No valid starting date could be found within more than a year time..")
            date_to_check = date_to_check - relativedelta(days=1)

    logger.info(f"Determined the first valid processable day to be: {date_to_check}")
    return date_to_check


def download_era5_file(
    dataset,
    product_type,
    grid_resolution,
    weather_factors,
    years,
    months,
    days,
    target_location,
):
    """
        A function that download a NetCDF file to the target location, containing the requested factors for an
        also requested range of years, months, days and locations.
    Args:
        dataset:            The name of the dataset to download from
        product_type:       The type of product to download
        grid_resolution:    The grid resolution to download the results in
        weather_factors:    A list of factors to be downloaded (in string format)
        years:              A list of years to be requested (numeric)
        months:             A list of months to be requested (numeric)
        days:               A list of days to be requested (numeric)
        target_location:    The file location to which the result should be saved after downloading.
    Returns:
        Returns nothing, but success means a result file will exist at the given target location.
    """
    c = downloader.CDSDownloadClient(persist_request_callback=_repository_callback(), verify=True)
    try:
        c.retrieve(
            dataset,
            {
                "product_type": product_type,
                "variable": weather_factors,
                "year": years,
                "month": months,
                "day": days,
                "time": [
                    "00:00",
                    "01:00",
                    "02:00",
                    "03:00",
                    "04:00",
                    "05:00",
                    "06:00",
                    "07:00",
                    "08:00",
                    "09:00",
                    "10:00",
                    "11:00",
                    "12:00",
                    "13:00",
                    "14:00",
                    "15:00",
                    "16:00",
                    "17:00",
                    "18:00",
                    "19:00",
                    "20:00",
                    "21:00",
                    "22:00",
                    "23:00",
                ],
                "area": [50.75, 3.2, 53.7, 7.22],
                "grid": [grid_resolution[0], grid_resolution[1]],
                "format": "netcdf",
            },
            target_location,
        )
    except Exception as e:
        logger.warning(f"Could not download the requested file: {e}")
        return False


def load_file(file: Path) -> xr.Dataset:
    """
        A function that loads and returns the full data for a specific repository file as a Xarray Dataset
    Args:
        file:   The filename (in the Path format by PathLib) specifying the file to load
    Returns:
        An Xarray Dataset containing all the weather data held within the specified file.

    """
    if file.exists():
        with xr.open_dataset(file) as ds:
            ds.load()
        return ds

    # Raise a FileNotFoundError if the file doesn't exist
    logger.error(f"File [{str(file)}] does not exist")
    raise FileNotFoundError


def _safely_delete_file(file: Path):
    """Basic function to safely remove files from the repository if possible, and supply errors if not"""
    try:
        logger.debug(f"Safely deleting file [{file}]")
        file.unlink()
    except OSError as e:
        logger.error(f"Could not safely delete file: {e}")
        raise OSError(f"Could not safely delete file: {file}")
    return True
