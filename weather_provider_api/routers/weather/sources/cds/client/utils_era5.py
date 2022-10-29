#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
from datetime import datetime
from pathlib import Path
from typing import List

import structlog
import xarray as xr
from dateutil.relativedelta import relativedelta

from weather_provider_api.routers.weather.repository.repository import RepositoryUpdateResult
from weather_provider_api.routers.weather.sources.cds.client import downloader
from weather_provider_api.routers.weather.sources.cds.factors import era5sl_factors

logger = structlog.get_logger(__name__)


def _repository_callback(*args, **kwargs):
    print("Callback - Received args:", args)
    print("Callback - Received kwargs:", kwargs)


def era5_update(
        file_prefix: str,
        first_day_of_repository: datetime,
        last_day_of_repository: datetime,
        runtime_limit: int,
        file_prefix_base: str,
        dataset_name: str,
        product_type: str,
        factors: List[str],
        grid_resolution: float
):
    update_start = datetime.utcnow()
    update_forced_end = update_start + relativedelta(seconds=runtime_limit)
    items_processed = 0
    average_time_per_item = 20 * 60  # Assuming 20 minutes of processing time for the first item

    logger.info(f'Starting update of repository {file_prefix}...', datetime=datetime.utcnow())

    active_month_for_update = last_day_of_repository.replace(day=1)
    while active_month_for_update >= first_day_of_repository:
        if items_processed != 0:
            average_time_per_item = (datetime.utcnow() - update_start).total_seconds() / items_processed

        if datetime.utcnow() + relativedelta(seconds=average_time_per_item) > update_forced_end:
            logger.info(f'There is not enough time remaining to process the next file. Finishing update routine..',
                        datetime=datetime.utcnow())
            return RepositoryUpdateResult.timed_out

        try:
            process_month(
                file_prefix_base=file_prefix_base,
                active_month_for_update=active_month_for_update,
                dataset=dataset_name,
                product_type=product_type,
                factors=factors,
                last_day_of_repo=last_day_of_repository,
                grid_resolution=grid_resolution
            )
        except Exception as e:
            logger.warning(str(e))
            logger.warning(f'Could not process year [{active_month_for_update.year}], '
                           f'month [{active_month_for_update.month}]', datetime=datetime.utcnow())

        items_processed += 1

        active_month_for_update -= relativedelta(months=1)

    return RepositoryUpdateResult.completed


def process_month(
        file_prefix_base: str,
        active_month_for_update: datetime,
        dataset: str,
        product_type: str,
        factors: List[str],
        last_day_of_repo: datetime,
        grid_resolution: float
):
    file_prefix = f'{file_prefix_base}_{active_month_for_update.year}_{str(active_month_for_update.month).zfill(2)}'

    if file_requires_update(file_prefix, last_day_of_repo):
        logger.debug(f'Updating the file for year [{active_month_for_update.year}], '
                     f'month [{active_month_for_update.month}]', datetime=datetime.utcnow())

        download_file = f'{file_prefix}_UNFORMATTED.nc'

        download_era5_file(
            dataset=dataset,
            product_type=product_type,
            grid_resolution=grid_resolution,
            weather_factors=factors,
            years=[active_month_for_update.year],
            months=[active_month_for_update.month],
            days=list(range(1, 32)),
            target_location=download_file
        )

        format_downloaded_file(download_file)

        Path(download_file).rename(f'{file_prefix}_FORMATTED.nc')

        finalize_formatted_file(file_prefix, last_day_of_repo)


def file_requires_update(file_prefix: str, last_day_of_repo: datetime):
    """
        A Function that checks if a file with a given prefix exists, and if it is a repository file that should
         be updated.
    Args:
        file_prefix:        The prefix of the filename to check. A file extension of .nc is assumed.
        last_day_of_repo:   The last day in the repository
    Returns:
        Returns True if the file should be updated, and False if no update is required.
    """
    if not glob.glob(file_prefix + "*.nc"):  # Globbing for all suffix
        return True  # No file exists yet, so must update!

    if Path(file_prefix + "_INCOMPLETE.nc").exists():
        return True  # File is or was the active month and is probably not completed yet. Must update

    if Path(file_prefix + "_TEMP.nc").exists():
        # If the file has the _TEMP suffix it only needs an update when it should've had a definitive update
        file_date = datetime(
            year=int(file_prefix[-7:-3]), month=int(file_prefix[-2:]), day=1
        )
        current_date_of_permanence = (
                last_day_of_repo
                - relativedelta(months=3)
        ).replace(day=1)

        # If the file is older than the three months required before permanence, it can be replaced by its permanent
        # version.
        if file_date < current_date_of_permanence:
            return True

    if Path(file_prefix + "_UNFORMATTED.nc").exists():
        # If somehow only an unformatted file exists, an update is definitely required
        return True

    return False


def format_downloaded_file(unformatted_file: str):
    """
        A function that formats an unformatted file
    Args:
        unformatted_file:   A string containing the full location of the unformatted file.
    Returns:
        Nothing. Completion is assumed to have generated
    """
    logger.debug(f"Formatting the downloaded file [{unformatted_file}]")
    ds_unformatted_data = load_file(Path(unformatted_file))

    # Delete attributes (purging excess metadata)
    ds_unformatted_data.attrs = {}

    if "expver" in ds_unformatted_data.indexes.keys():
        # While in v3.0 we want to keep the difference between expver versions, in 2.x the difference between
        # validated and not yet validated data is not used.
        # Therefor we split the data up in two sets while dropping expver and NaN values and then recombining them
        ds_unformatted_data_expver_1 = ds_unformatted_data.sel(expver=1).drop_sel('expver').dropna('time', how='all')
        ds_unformatted_data_expver_5 = ds_unformatted_data.sel(expver=5).drop_sel('expver').dropna('time', how='all')

        # Recombine data
        ds_unformatted_data = ds_unformatted_data_expver_1.merge(ds_unformatted_data_expver_5)

    # Rename factors to their longer names
    for factor in ds_unformatted_data.variables.keys():
        if factor in era5sl_factors:
            ds_unformatted_data = ds_unformatted_data.rename_vars({factor: era5sl_factors[factor]})
    ds_unformatted_data.time.encoding["units"] = "hours since 2016-01-01"
    ds_unformatted_data = ds_unformatted_data.rename(name_dict={"latitude": "lat", "longitude": "lon"})
    ds_unformatted_data.to_netcdf(path=unformatted_file, format="NETCDF4", engine="netcdf4")


def download_era5_file(
        dataset, product_type, grid_resolution, weather_factors, years, months, days, target_location
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
    c = downloader.Client(
        persist_request_callback=_repository_callback(), debug=True, verify=True
    )
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
            "grid": [grid_resolution, grid_resolution],
            "format": "netcdf",
        },
        target_location,
    )


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
    logger.error(
        f"File [{str(file)} does not exist]", datetime=datetime.utcnow()
    )
    raise FileNotFoundError


def finalize_formatted_file(file_prefix: str, last_day_of_repo: datetime):
    """
        A function that finalizes a formatted file by renaming it into the proper suffix (or lack thereof) for its
        type.
        No Suffix:      Permanent File
        _INCOMPLETE:    Incomplete file for the currently being processed month.
        _TEMP:          Complete file using not yet verified values. Data is confirmed or replaced in about three
                        months by the permanent data.
    Args:
        file_prefix:    The prefix for the file to verify. Does not include the assumed "_FORMATTED.nc" suffix and
                        file extension.
        last_day_of_repo: The last day of the repository, used to determine incomplete months.
    Returns:
        Doesn't return anything, but renames the _FORMATTED.nc file as appropriate for the data in it, based on
        data age.
    """
    # First we verify that the formatted file exists
    if not Path(file_prefix + "_FORMATTED.nc").exists():
        logger.error(
            f"A formatted file for [{file_prefix}] was not found",
            datetime=datetime.utcnow(),
        )
        raise FileNotFoundError(
            f"A formatted file for [{file_prefix}] was not found"
        )

    if Path(file_prefix + "_TEMP.nc").exists():
        _safely_delete_file(file_prefix + "_TEMP.nc")
    if Path(file_prefix + "_INCOMPLETE.nc").exists():
        _safely_delete_file(file_prefix + "_INCOMPLETE.nc")

    file_date = datetime(
        year=int(file_prefix[-7:-3]), month=int(file_prefix[-2:]), day=1
    )
    current_incomplete_month = last_day_of_repo.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    oldest_temporary_month = current_incomplete_month - relativedelta(months=3)

    if current_incomplete_month == file_date:
        # If currently processing the incomplete month, rename it as such
        Path(file_prefix + "_FORMATTED.nc").rename(file_prefix + "_INCOMPLETE.nc")
    elif oldest_temporary_month < file_date < current_incomplete_month:
        # If currently processing a temporary file that is not incomplete, rename it as such
        Path(file_prefix + "_FORMATTED.nc").rename(file_prefix + "_TEMP.nc")
    else:
        # If currently processing a permanent file, rename it as such
        Path(file_prefix + "_FORMATTED.nc").rename(file_prefix + ".nc")


def _safely_delete_file(file: str):
    """ Basic function to safely remove files from the repository if possible, and supply errors if not """
    try:
        logger.debug(
            f"Safely deleting file [{file}]", datetime=datetime.utcnow()
        )
        Path(file).unlink()
    except OSError as e:
        logger.error(f"Could not safely delete file: {e}")
        raise OSError(f"Could not safely delete file: {file}")
    return True
