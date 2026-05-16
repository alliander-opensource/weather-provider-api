#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""This module houses the repository class for the Actuele Waarnemingen Register."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import xarray as xr
from loguru import logger

from weather_provider_api.routers.weather.repository.repository import (
    RepoDataFetchResult,
    RepoUpdateResult,
    WeatherRepositoryBase,
    WeatherRepositoryConfiguration,
)
from weather_provider_api.routers.weather.sources.knmi.utils.commons import download_actuele_waarnemingen_weather
from weather_provider_api.routers.weather.utils.date_helpers import subtract_months


class ActueleWaarnemingenRegisterRepository(WeatherRepositoryBase):
    """Repository class for the KNMI Actuele Waarnemingen - 48 uur register."""

    def __init__(self):
        """Initializes the repository, setting all settings and variables needed for the repository to function."""
        # Pre-work
        super().__init__(
            WeatherRepositoryConfiguration(
                identifier="KNMI Actuele Waarnemingen - 48 uur register",
                storage_path=Path("knmi/actueel48"),
                storage_states={"raw", "processed"},
                maximum_runtime_seconds=60 * 3,  # 3 minutes
                temporal_file_identifier="",
                affiliated_source_and_model=("knmi", "actueel48"),
            )
        )
        self.storage_filename: Path = (
            self.absolute_storage_path
            / f"{self.source_and_model['source']}_{self.source_and_model['model']}_registry.nc"
        )
        logger.info(f"Initialized {self.__class__.__name__} with configuration:\n{self.metadata}")

    @property
    def oldest_date_available(self) -> date:
        """Return the oldest date for which data is available."""
        oldest_datetime = datetime.now(UTC).date() - timedelta(days=2)  # Two days back
        return oldest_datetime

    @property
    def newest_date_available(self) -> date:
        """Return the newest date for which data is available."""
        return date.today()

    def update(self, *, run_in_testmode: bool = False) -> tuple[RepoUpdateResult, str]:
        """Implementation of the WeatherRepository update method.

        Attempts to update the repository with the current data. For this repository, that means getting the current
         Actuele Waarnemingen output and storing it, while removing any data not within the scope of the repository.

        Returns:
            RepoUpdateResult:
                    An enum indicating the result of the update attempt.
            str:
                    A message providing additional information about the update result.

        """
        raw_weather_dataset = download_actuele_waarnemingen_weather()
        current_moment = datetime.now(UTC).replace(second=0, microsecond=0)

        # Cleanup any old data
        self.cleanup_storage()

        # Update the file
        self._update_file_with_new_data(new_data_ds=raw_weather_dataset, update_moment=current_moment)

        return RepoUpdateResult.SUCCESS, "Update method not implemented yet for this repository."

    def cleanup_storage(self) -> RepoUpdateResult:
        """Clean up the storage by removing or archiving old or deprecated files."""
        return self._delete_files_outside_of_scope()

    def _update_file_with_new_data(self, new_data_ds: xr.Dataset, update_moment: datetime) -> RepoDataFetchResult:
        """This method updates any existing data file with new data.

        If the file doesn't exist, it will be created. If the file does exist, the new data will be merged with the existing
        data, ensuring that there are no duplicate time entries. The file will then be saved with the merged data.

        Args:
            new_data_ds (xr.Dataset):   A Xarray Dataset holding the data to append / create the data file with.
            update_moment (datetime):   A datetime holding the moment of update. Note that this doesn't need to be the
                                        moment that the data is from.

        Returns:
            RepoDataFetchResult: An enum indicating the result of the data fetch attempt.

        """
        storage_dataset: xr.Dataset | None = None
        if self.storage_filename.exists():
            logger.info(f"Trying to load ")
            try:
                storage_dataset = xr.load_dataset(self.storage_filename, engine="netcdf4", format="NETCDF4")  # type: ignore
            except Exception as e:
                logger.error(f"An error occured while trying to open the existing file: {e}")
                logger.info("Attempting to delete existing file to create a new one")
                self.safely_delete_file(self.storage_filename)
                storage_dataset = None

        logger.info(f"Storing new data retrieved at [{update_moment}] into file")
        
        if storage_dataset is None:
            # New file
            new_data_ds.to_netcdf(self.storage_filename, engine="netcdf4", format="NETCDF4")
            return RepoDataFetchResult.SUCCESS
        
        # Existing file
         

            # Check if time not already in system
    #         try:
    #             new_stored_data_ds = xr.merge([new_data_ds, stored_data_ds])

    #             new_stored_data_ds.to_netcdf(self.filename, format="NETCDF4")
    #         except ValueError as value_error:
    #             logger.error(f"Could not update file: {value_error}")

        return RepoDataFetchResult.SUCCESS

    # def _update_file_with_new_data(self, new_data_ds: xr.Dataset, update_moment: datetime):
    #     """This method updates any existing data file with new data or creates a new from scratch if needed, using the
    #      given dataset.

    #     Args:
    #         new_data_ds (xr.Dataset):   A Xarray Dataset holding the data to append / create the data file with.
    #         update_moment (datetime):   A datetime holding the moment of update. Note that this doesn't need to be the
    #                                      moment that the data is from.

    #     Returns:
    #         Nothing. The file is just updated.

    #     """
    #     # Opening the file:
    #     if self.filename.exists():
    #         stored_data_ds = xr.load_dataset(self.filename, engine="netcdf4")
    #     else:
    #         stored_data_ds = None

    #     logger.info(
    #         f"Storing data at [{update_moment.strftime('%m-%d-%Y %H:%M:%S')}] for "
    #         f"[{new_data_ds.isel(STN=0, time=0)['time'].values}]"
    #     )
    #     if stored_data_ds is None:
    #         new_data_ds.to_netcdf(self.filename, format="NETCDF4")
    #     else:
    #         # Check if time not already in system
    #         try:
    #             new_stored_data_ds = xr.merge([new_data_ds, stored_data_ds])

    #             new_stored_data_ds.to_netcdf(self.filename, format="NETCDF4")
    #         except ValueError as value_error:
    #             logger.error(f"Could not update file: {value_error}")

    # def get_24_hour_registry_for_station(self, station: int) -> xr.Dataset:
    #     """This method obtains the last 24 hours of data of Actuele Waarnemingen and returns it for single station.

    #     Args:
    #         station (int):  An integer representing the station to gather data for

    #     Returns:
    #         xr.Dataset: A Xarray Dataset holding last 24 hours of data for the requested station

    #     """
    #     stored_data_ds = xr.load_dataset(self.filename, engine="netcdf4")
    #     return stored_data_ds.sel(
    #         STN=station,
    #         time=slice(self.first_day_of_repo + relativedelta(days=1), self.last_day_of_repo),
    #     )

    # def get_48_hour_registry_for_station(self, station: int) -> xr.Dataset:
    #     """This method obtains the last 48 hours of data of Actuele Waarnemingen and returns it for single station.

    #     Args:
    #         station (int):  An integer representing the station to gather data for

    #     Returns:
    #         xr.Dataset: A Xarray Dataset holding last 48 hours of data for the requested station

    #     """
    #     stored_data_ds = xr.load_dataset(self.filename, engine="netcdf4")
    #     stored_data_ds = stored_data_ds.sel(
    #         STN=station,
    #         time=slice(self.first_day_of_repo, self.last_day_of_repo),
    #     )
    #     return stored_data_ds

    def _delete_files_outside_of_scope(self) -> RepoUpdateResult:
        logger.info(f"Deleting files outside of scope [{self.oldest_date_available} - {self.newest_date_available}]")
        if self.storage_filename.exists():
            try:
                current_data = xr.load_dataset(self.storage_filename, engine="netcdf4")  # type: ignore
            except OSError as os_error:
                logger.error(
                    f"Could not load file for cleanup: {os_error}. File is likely corrupted and will be deleted."
                )
                self.storage_filename.unlink(missing_ok=True)
                return RepoUpdateResult.FAILURE
            current_data = current_data.sel(time=slice(self.oldest_date_available, self.newest_date_available))
            current_data.to_netcdf(self.storage_filename, format="NETCDF4")  # type: ignore

            return RepoUpdateResult.SUCCESS

        return (
            RepoUpdateResult.SUCCESS
        )  # If file doesn't exist, we can consider it a success as there's nothing outside of scope

    def get_existing_files_in_repository(self) -> list[dict[str, str | Path]]:
        """Get the existing files in the repository.

        This method returns a list of dictionaries containing information about the files that are currently stored
        in the repository. For this repository, there will be at most one file, which is the current
        Actuele Waarnemingen registry file.

        Returns:
            list[dict[str, str | Path]]:
                    A list of dictionaries, each containing 'name', 'datetime_tag', 'state', and 'path' of a file in
                    the repository.

        """
        if self.storage_filename.exists():
            return [
                {
                    "name": self.storage_filename.name,
                    "datetime_tag": "",  # No datetime tag for this repository as it only holds one file
                    "state": "processed",  # Assuming the file is always in processed state after being stored
                    "path": self.storage_filename,
                }
            ]
        else:
            return []

    # def _get_file_list_for_period(self, start: datetime, end: datetime):
    #     return self.storage_filename
