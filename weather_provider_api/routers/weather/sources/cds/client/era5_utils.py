# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import glob
import tempfile
import zipfile
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from pathlib import Path

import xarray as xr
from loguru import logger
from pydantic import BaseModel

from weather_provider_api.routers.weather.base_models.repository import RepoUpdateResult
from weather_provider_api.routers.weather.sources.cds.client.cds_api_tools import CDS_CLIENT, CDSDataSets, CDSRequest
from weather_provider_api.routers.weather.utils.date_helpers import subtract_months


class Era5FileSuffixes(StrEnum):
    """Enum class for the different suffixes that can be used for the ERA5 files."""

    FORMATTED = ".FORMATTED.nc"
    UNFORMATTED = ".UNFORMATTED.nc"
    INCOMPLETE = ".INCOMPLETE.nc"
    TEMP = ".TEMP.nc"


class Era5UpdateSettings(BaseModel):
    """A class that holds the settings for updating the ERA5 data."""

    era5_dataset_to_update_from: CDSDataSets
    era5_product_type: str | None
    filename_prefix: str
    target_storage_location: Path
    repository_time_range: tuple[date, date]
    factors_to_process: list[str]
    factor_dictionary: dict[str, str]
    maximum_runtime_in_minutes: int = 2 * 60  # 2 hours


def era5_repository_update(update_settings: Era5UpdateSettings, test_mode: bool) -> tuple[RepoUpdateResult, str]:
    """A function to update a variant of ERA5 data into the repository."""
    starting_moment_of_update = datetime.now(UTC)
    cutoff_time = starting_moment_of_update + timedelta(minutes=update_settings.maximum_runtime_in_minutes)
    logger.info(
        f"Starting update of ERA5 data for {update_settings.era5_dataset_to_update_from} "
        f"to: {update_settings.target_storage_location}"
    )
    logger.debug(f" - Attempting update for time range: {update_settings.repository_time_range}")
    logger.debug(f" - Factors to process: {update_settings.factors_to_process}")
    logger.info(f" - Maximum runtime: {update_settings.maximum_runtime_in_minutes} minutes ({cutoff_time})")

    try:
        _era5_update_month_by_month(update_settings, starting_moment_of_update, cutoff_time, test_mode)
    except Exception as e:
        logger.error(f"Failed to update ERA5 data. Reason: {e}")
        return RepoUpdateResult.FAILURE, str(e)

    ending_moment_of_update = datetime.now(UTC)
    logger.info(
        f"Update finished. Total runtime: {(ending_moment_of_update - starting_moment_of_update).total_seconds()}"
    )
    return RepoUpdateResult.SUCCESS, "Repository is up to date."


def _era5_update_month_by_month(
    update_settings: Era5UpdateSettings, starting_moment_of_update: datetime, cutoff_time: datetime, test_mode: bool
):
    """A function to update a variant of ERA5 data into the repository."""
    amount_of_months_processed = amount_of_months_not_processable = 0
    average_time_per_month_in_minutes = 35

    update_month = _get_update_month(update_settings)
    target_update_month = update_settings.repository_time_range[0].replace(day=1)

    while update_month > target_update_month:
        logger.info(f" > Processing month: {update_month.year}-{update_month.month}")
        if datetime.now(UTC) + timedelta(minutes=average_time_per_month_in_minutes) > cutoff_time:
            logger.warning(
                "MAXIMUM RUNTIME REACHED: ",
                cutoff_time,
                datetime.now(UTC) + timedelta(minutes=average_time_per_month_in_minutes),
                average_time_per_month_in_minutes,
            )
            logger.warning("Maximum runtime reached. Stopping update.")
            break

        update_result = _era5_update_month(update_settings, update_month, test_mode)
        if update_result == RepoUpdateResult.FAILURE:
            amount_of_months_not_processable += 1
        amount_of_months_processed += 1

        if amount_of_months_not_processable / amount_of_months_processed > 0.5:
            logger.warning("More than 50% of the months failed to process. Stopping update.")
            break

        average_time_per_month_in_minutes = int(
            (datetime.now(UTC) - starting_moment_of_update).total_seconds() / 60 / amount_of_months_processed
        )

        update_month = subtract_months(update_month, 1)

    logger.info(
        f"Processed {amount_of_months_processed} months, {amount_of_months_not_processable} months failed to process."
    )
    logger.info(f"Average time per month: {average_time_per_month_in_minutes} minutes")


def _era5_update_month(update_settings: Era5UpdateSettings, update_month: date, test_mode: bool) -> RepoUpdateResult:
    """A function to update a variant of ERA5 data into the repository."""
    logger.debug(f" > Processing month: {update_month.year}-{update_month.month}")

    month_file_base = f"{update_settings.filename_prefix}_{update_month.year}_{update_month.month:02d}"
    month_file = update_settings.target_storage_location / f"{month_file_base}"
    threshold_date = (datetime.now(UTC) - timedelta(days=5)).replace(day=1).date()

    if file_requires_update(month_file, update_month, threshold_date):
        logger.debug(f" > File {month_file} requires update.")
        month_file_name = month_file.with_suffix(Era5FileSuffixes.UNFORMATTED)

        # Only the first day of each month in test mode, otherwise all days:
        day = [str(i) for i in range(1, 32)] if not test_mode else ["1"]

        try:
            download_era5_data(
                update_settings.era5_dataset_to_update_from,
                CDSRequest(
                    product_type=[update_settings.era5_product_type]
                    if update_settings.era5_product_type is not None
                    else None,
                    variables=update_settings.factors_to_process,
                    year=[str(update_month.year)],
                    month=[str(update_month.month)],
                    day=day,
                    time=[f"{hour:02d}:00" for hour in range(24)],
                ),
                target_location=str(month_file_name),
            )

            logger.debug("Stored file at: ", month_file_name)

            if update_settings.era5_dataset_to_update_from == CDSDataSets.ERA5SL:
                # We need to recombine multiple files into one for ERA5SL, as the data is split into multiple files
                _recombine_multiple_files(month_file_name)
            elif update_settings.era5_dataset_to_update_from == CDSDataSets.ERA5LAND:
                # Unpack the file
                temp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(month_file_name, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)
                # Save the data_0.nc file to the month_file_name location
                data_file = Path(temp_dir).joinpath("data_0.nc")
                data_file.rename(month_file_name)

            _format_downloaded_file(month_file_name, update_settings.factor_dictionary)

            month_file_name.rename(month_file.with_suffix(Era5FileSuffixes.FORMATTED))
            logger.debug("Renamed to: ", month_file.with_suffix(Era5FileSuffixes.FORMATTED))
            _finalize_formatted_file(month_file, update_month, threshold_date)

        except Exception as e:
            logger.error(f" > Failed to update ERA5 data for {update_month}. Reason: {e}")
            return RepoUpdateResult.FAILURE

    return RepoUpdateResult.SUCCESS


def _get_update_month(update_settings: Era5UpdateSettings) -> date:
    _normal_first_moment_available_for_era5 = (datetime.now(UTC) - timedelta(days=5)).date()
    update_moment = update_settings.repository_time_range[1]

    update_moment = (
        update_moment
        if update_moment < _normal_first_moment_available_for_era5
        else _normal_first_moment_available_for_era5
    )

    if update_moment == _normal_first_moment_available_for_era5:
        update_moment = _verify_first_day_available_for_era5(update_moment, update_settings)

    update_moment = update_moment.replace(day=1)
    return update_moment


def _verify_first_day_available_for_era5(update_moment: date, update_settings: Era5UpdateSettings) -> date:
    """A function to verify the first day available for ERA5 data.

    Normally the first full day available for ERA5 data is the 5 days ago, however, due to the nature of the data
    it might be that data takes longer to fully process and be available. This function will verify if the data is
    available and if not, will return the correct first day available.
    """
    logger.debug(" > Verifying the first day available for ERA5 data.")

    while True:
        try:
            download_era5_data(
                dataset=update_settings.era5_dataset_to_update_from,
                cds_request=CDSRequest(
                    product_type=[update_settings.era5_product_type]
                    if update_settings.era5_product_type is not None
                    else None,
                    variables=["soil_temperature_level_1"],  # A factor that exists in all supported ERA5 datasets
                    year=[str(update_moment.year)],
                    month=[str(update_moment.month)],
                    day=[str(update_moment.day)],
                    time=[f"{hour:02d}:00" for hour in range(2)],
                ),
                target_location=tempfile.NamedTemporaryFile().name,
            )
            break
        except Exception as e:
            logger.debug(f" > Failed to download ERA5 data for {update_moment}. Reason: {e}")
            update_moment = update_moment - timedelta(days=1)

            if update_moment < update_settings.repository_time_range[1] - timedelta(days=45):
                raise ValueError(
                    "The first day available for ERA5 data could not be found within 40 days of the target date. "
                    "Aborting update."
                ) from e

    return update_moment


def _finalize_formatted_file(file_path: Path, current_moment: date, verification_date: date) -> None:
    """A function to finalize the formatted file."""
    # Ensure verification_date is a datetime (if it's a date, convert to datetime)
    incomplete_month = verification_date.replace(day=1)
    permanent_month = subtract_months(verification_date, 3)

    if not file_path.with_suffix(Era5FileSuffixes.FORMATTED).exists():
        logger.error(f"Formatted file {file_path} does not exist. Aborting finalization.")
        raise FileNotFoundError(f" > Formatted file {file_path} does not exist.")

    # Cleanup the old files
    for file_suffix in [Era5FileSuffixes.TEMP, Era5FileSuffixes.INCOMPLETE]:
        if file_path.with_suffix(file_suffix).exists():
            try:
                file_path.with_suffix(file_suffix).unlink()
            except Exception as e:
                logger.error(f" > Failed to remove temporary file {file_path.with_suffix(file_suffix)}: {e}")

    # Rename the file to its proper name:
    if current_moment == verification_date.replace(day=1):
        # Current month means an incomplete file
        file_path.with_suffix(Era5FileSuffixes.FORMATTED).rename(file_path.with_suffix(Era5FileSuffixes.INCOMPLETE))
        logger.debug(f"Month [{current_moment}] was renamed to: {file_path.with_suffix(Era5FileSuffixes.INCOMPLETE)}")
    elif permanent_month < current_moment < incomplete_month:
        # Non-permanent file
        file_path.with_suffix(Era5FileSuffixes.FORMATTED).rename(file_path.with_suffix(Era5FileSuffixes.TEMP))
        logger.debug(f"Month [{current_moment}] was renamed to: {file_path.with_suffix(Era5FileSuffixes.TEMP)}")
    else:
        # Permanent file
        file_path.with_suffix(Era5FileSuffixes.FORMATTED).rename(file_path.with_suffix(".nc"))
        logger.debug(f"Month [{current_moment}] was renamed to: {file_path.with_suffix('.nc')}")


def file_requires_update(file_path: Path, current_month: date, verification_date: date) -> bool:
    """A function that checks if a file requires an update based on the current state of the repository."""
    if file_path.with_suffix(Era5FileSuffixes.TEMP).exists():
        # If a file is temporary we only check for a permanent update if more than 3 months have past since the current
        # most recent date with data.
        threshold_date = subtract_months(verification_date, 3)
        if current_month < threshold_date:
            logger.debug(" > A temporary file exists within the update range: UPDATE REQUIRED")
            return True
        logger.debug(" > A temporary file exists within the update range: UPDATE REQUIRED")
        return False

    # A file exists but isn't any regular supported type to be updated
    if (
        file_path.with_suffix(Era5FileSuffixes.UNFORMATTED).exists()
        or file_path.with_suffix(Era5FileSuffixes.FORMATTED).exists()
    ):
        logger.debug(" > An unformatted file or formatted file exists: UPDATE REQUIRED")
        return True  # An update should both clean the UNFORMATTED file and generate a proper one

    if not file_path.with_suffix(".nc").exists() or file_path.with_suffix(Era5FileSuffixes.INCOMPLETE).exists():
        logger.debug(" > No file exists, or it is still incomplete: UPDATE REQUIRED")
        return True  # No file matching the mask or incomplete files always mean the update is required!

    if file_path.with_suffix(".nc").exists():
        # A regular file exists, no updates required
        logger.debug(" > A regular file already exists: NO UPDATE REQUIRED")
        return False
    files_in_folder = glob.glob(f"{file_path}*.nc")
    logger.warning(
        f" > Unexpected files existed in the repository folder: {files_in_folder}. These should be dealt with."
    )
    return False


def _format_downloaded_file(unformatted_file: Path, allowed_factors: dict[str, str]) -> None:
    """A function that formats the downloaded file to the correct format for the repository."""
    logger.info(f" > Formatting the downloaded file at: {unformatted_file}")
    ds_unformatted = load_file(unformatted_file)
    ds_unformatted.attrs = {}  # Remove unneeded attributes

    if "expver" in ds_unformatted.indexes:
        # We remove the expver index used to denominate temporary data (5) and regular data (1) and add a field for it
        # NOTE: We removed the drop_sel version as it didn't quite have the same result as drop yet. Reverting until
        #  the proper use has been validated...
        ds_unformatted_expver5 = (
            ds_unformatted.sel(expver=5)
            .drop("expver")
            .dropna(  # type: ignore
                "valid_time", how="all"
            )
        )
        ds_unformatted_expver1 = (
            ds_unformatted.sel(expver=1)
            .drop("expver")
            .dropna(  # type: ignore
                "valid_time", how="all"
            )
        )

        # Recombine the data
        expver_unformatted_dataset: xr.Dataset = ds_unformatted_expver1.merge(ds_unformatted_expver5)  # type: ignore
        expver_unformatted_dataset["is_permanent_data"] = False
    else:
        expver_unformatted_dataset = ds_unformatted.copy(deep=True)
        expver_unformatted_dataset["is_permanent_data"] = True

    # Rename the factors to their longer names:
    for factor in expver_unformatted_dataset.variables:
        factor_str = str(factor)
        if factor_str in allowed_factors:
            expver_unformatted_dataset = expver_unformatted_dataset.rename_vars(
                {factor_str: allowed_factors[factor_str]}
            )

    # Rename and encode data where needed:
    expver_unformatted_dataset.valid_time.encoding["units"] = "hours since 2016-01-01"
    expver_unformatted_dataset = expver_unformatted_dataset.rename(
        name_dict={"latitude": "lat", "longitude": "lon", "valid_time": "time"}
    )

    # Store the data
    expver_unformatted_dataset.to_netcdf(path=unformatted_file, format="NETCDF4", engine="netcdf4", mode="w")  # type: ignore


def load_file(file: Path) -> xr.Dataset:
    """A function that loads and returns the full data for a specific repository file as a Xarray Dataset.

    Args:
        file:   The filename (in the Path format by PathLib) specifying the file to load
    Returns:
        An Xarray Dataset containing all the weather data held within the specified file.

    """
    if file.exists():
        with xr.open_dataset(file, engine="netcdf4") as ds:  # type: ignore
            ds.load()  # type: ignore
        return ds

    # Raise a FileNotFoundError if the file doesn't exist
    logger.error(f" > File [{file!s}] does not exist")
    raise FileNotFoundError


def _recombine_multiple_files(unformatted_file: Path) -> None:
    """A function that recombines multiple files into one."""
    logger.debug(f" > Recombining multiple files for: {unformatted_file}")

    # Create a temporary directory to store the files
    temp_dir = tempfile.mkdtemp()

    # Unpack the file
    with zipfile.ZipFile(unformatted_file, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    files_to_load_in_order = [
        "data_stream-oper_stepType-instant",
        "data_stream-oper_stepType-accum",
        # TODO: Add the following file back in when we can properly handle it
        # "data_stream-wave_stepType-instant",  # Something about this data doesn't mesh well anymore with the rest...
    ]

    concatenated_dataset = xr.Dataset()
    for filename in files_to_load_in_order:
        file_path = Path(temp_dir).joinpath(f"{filename}.nc")
        if not file_path.exists():
            logger.error(f" > Required file {filename}.nc does not exist. Aborting recombination.")
            raise FileNotFoundError(f" > Required file {filename}.nc does not exist. Aborting recombination.")

        dataset = xr.open_dataset(file_path)  # type: ignore
        dataset = dataset.drop("expver", errors="raise")  # type: ignore

        if not concatenated_dataset.data_vars:
            concatenated_dataset = dataset.copy(deep=True)
        else:
            concatenated_dataset = xr.merge(  # type: ignore
                [concatenated_dataset, dataset], join="outer", compat="no_conflicts", combine_attrs="override"
            )

    concatenated_dataset.to_netcdf(unformatted_file, format="NETCDF4", engine="netcdf4")  # type: ignore


def download_era5_data(
    dataset: CDSDataSets,
    cds_request: CDSRequest,
    target_location: str,
) -> None:
    """A function to download ERA5 data."""
    try:
        CDS_CLIENT.retrieve(  # type: ignore
            name=dataset.value,
            request=cds_request.request_parameters,
            target=target_location,
        )

    except Exception as e:
        logger.error(f"Failed to download ERA5 data. Reason: {e}")
        raise e
