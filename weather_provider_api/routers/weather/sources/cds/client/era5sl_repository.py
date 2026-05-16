#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import calendar
import glob
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
from weather_provider_api.routers.weather.sources.cds.client.cds_api_tools import CDSDataSets
from weather_provider_api.routers.weather.sources.cds.client.era5_utils import (
    Era5UpdateSettings,
    era5_repository_update,
)
from weather_provider_api.routers.weather.sources.cds.factors import era5sl_factors
from weather_provider_api.routers.weather.utils.date_helpers import subtract_months


class ERA5SLRepository(WeatherRepositoryBase):
    """A class that holds all functionality (excepting the downloader) for the ERA5 Single Levels Repository."""

    def __init__(self):
        """Initializes the ERA5 Single Levels Repository."""
        super().__init__(
            WeatherRepositoryConfiguration(
                identifier="CDS ERA5 Single Levels",
                storage_path=Path("cds/era5sl"),
                storage_states={"raw", "processed", "uncertain", "incomplete"},
                maximum_runtime_seconds=60 * 60 * 3,  # 3 hours
                temporal_file_identifier="%Y%m%d",
                affiliated_source_and_model=("cds", "era5sl"),
            )
        )

        self.cds_dataset = CDSDataSets.ERA5SL
        self.cds_product_type = "reanalysis"
        self.factors_to_process = era5sl_factors.keys()
        self.years_to_store = 10

        logger.info(f"Initialized {self.__class__.__name__} with configuration:\n{self.metadata}")

    @property
    def oldest_date_available(self) -> date:
        """Returns the oldest date for which data is available in the repository."""
        oldest_day_in_repo = subtract_months(datetime.now(UTC).date(), self.years_to_store * 12) - timedelta(days=5)
        return oldest_day_in_repo

    @property
    def newest_date_available(self) -> date:
        """Returns the newest date for which data is available in the repository."""
        return (datetime.now(UTC).date() - timedelta(days=5))

    def update(self, *, run_in_testmode: bool = False) -> tuple[RepoUpdateResult, str]:
        """Update the repository with new data."""
        msg = f"Updating {self.identifier} repository"
        if run_in_testmode:
            msg += " (test mode)"
        logger.info(msg)

        # Start by cleaning up the repository to ensure a good state before updating
        if self.cleanup_storage() == RepoUpdateResult.FAILURE:
            logger.error(
                "Failed to clean up the repository storage. Aborting update to avoid potential data integrity issues."
            )
            return RepoUpdateResult.FAILURE, "Failed to clean up the repository storage."

        # process the update and return the result
        return era5_repository_update(
            update_settings=Era5UpdateSettings(
                filename_prefix="cds_era5sl",
                era5_dataset_to_update_from=self.cds_dataset,
                era5_product_type=self.cds_product_type,
                factor_dictionary=era5sl_factors,
                factors_to_process=[era5sl_factors[x] for x in self.factors_to_process],
                maximum_runtime_in_minutes=int(self.config.maximum_runtime_seconds // 60),
                repository_time_range=(self.oldest_date_available, self.newest_date_available),
                target_storage_location=self.absolute_storage_path,
            ),
            test_mode=run_in_testmode,
        )

    def cleanup_storage(self) -> RepoUpdateResult:
        """Cleans up the storage by deleting all files that are outside of the repository's scope."""
        self._delete_files_outside_of_scope()

        return RepoUpdateResult.SUCCESS

    def _delete_files_outside_of_scope(self):
        """A function that deletes all files in the repository with a date not inside the repository's scope.

        All files labeled as either before or after the given scope will be deleted.

        Returns:
            Nothing. Successful means the all files outside the scope were deleted.
        """
        prefix = str(self.absolute_storage_path / "cds_era5sl_")
        prefix_len = len(prefix)
        for file_path in glob.glob(f"{prefix}*.nc"):
            # Expecting filenames like .../cds_era5sl_YYYY-MM.nc
            try:
                year = int(file_path[prefix_len : prefix_len + 4])
                month = int(file_path[prefix_len + 5 : prefix_len + 7])
                file_date = date(year, month, 1)
            except (ValueError, IndexError):
                logger.warning(f"Skipping file with unexpected name format: {file_path}")
                continue

            if not self.oldest_date_available <= file_date <= self.newest_date_available:
                logger.debug(
                    f"Deleting file [{file_path}] because it does not lie in the "
                    f"repository scope ({self.oldest_date_available}, {self.newest_date_available})"
                )
                self.safely_delete_file(Path(file_path))


    def retrieve_data(self, from_date: date, to_date: date, locations: list[tuple[float, float]], factors: list[str]) -> tuple[xr.Dataset | None, RepoDataFetchResult]:
        """Retrieves data from the repository for the given parameters."""
        required_files_for_data = self._retrieve_files_matching_period(from_date, to_date)

        try:
            combined_dataset = self._gather_data_from_files_and_combine_into_dataset(required_files_for_data, locations, factors)
        except Exception as e:
            logger.error(f"An error occurred while retrieving data: {e}")
            return None, RepoDataFetchResult.FAILURE

        return combined_dataset, RepoDataFetchResult.SUCCESS

    def _retrieve_files_matching_period(self, from_date: date, to_date: date) -> list[Path]:
        """A function that retrieves a list of files in the repository associated with the requested period of time.

        Args:
            from_date:  A datetime containing the start of the requested period of time.
            to_date:    A datetime containing the end of the requested period of time.

        Returns:
            A list of files (in string format) that indicate the files containing data for the requested period.
        """
        prefix = str(self.absolute_storage_path / "cds_era5sl_")
        prefix_len = len(prefix)
        last_day_of_end_month = to_date.replace(day=calendar.monthrange(to_date.year, to_date.month)[1]).day
        list_of_required_files: list[Path] = []
        
        for file_path in glob.glob(f"{prefix}*.nc"):
            # Expecting filenames like .../cds_era5sl_YYYY-MM.nc
            try:
                year = int(file_path[prefix_len : prefix_len + 4])
                month = int(file_path[prefix_len + 5 : prefix_len + 7])
                file_date = date(year, month, 1)
            except (ValueError, IndexError):
                logger.warning(f"Skipping file with unexpected name format: {file_path}")
                continue

            if from_date.replace(day=1) <= file_date <= to_date.replace(day=last_day_of_end_month):
                # If the file is within the requested period, save it to the list of filtered files
                logger.debug(f"Adding file [{file_path}] to the list of files for the requested period.")
                list_of_required_files.append(Path(file_path))

        return list_of_required_files

    def _gather_data_from_files_and_combine_into_dataset(
        self,
        required_files_for_data: list[Path],
        locations: list[tuple[float, float]],
        factors: list[str],
    ) -> xr.Dataset | None:
        """Gather data from the required files and combine it into a single Dataset.

        Arguments:
            required_files_for_data:
                    A list of Path objects representing the files that match the specified date range.
            locations:
                    A list of tuples containing the latitude and longitude of the locations for which data is requested.
            factors:
                    A list of strings representing the factors to be included in the dataset.
        """
        combined_dataset: xr.Dataset | None = None

        for file_path in required_files_for_data:
            try:
                dataset: xr.Dataset = xr.open_dataset(file_path, engine="netcdf4", mode="r")  # type: ignore
                filtered_dataset = self._filter_dataset_by_locations_and_factors(dataset, locations, factors)
                if combined_dataset is None:
                    combined_dataset = filtered_dataset
                else:
                    combined_dataset = xr.concat([combined_dataset, filtered_dataset], dim="time")
            except Exception as e:
                logger.error(f"An error occurred while reading file [{file_path}]: {e}")
                raise e

        if not combined_dataset:
            logger.warning("No data could be read from the required files. Returning None.")
            return None
        return combined_dataset

    def _filter_dataset_by_locations_and_factors(
        self, dataset: xr.Dataset, locations: list[tuple[float, float]], factors: list[str]
    ) -> xr.Dataset:
        """Filter the dataset based on the requested locations and factors.

        Arguments:
            dataset:
                    An xarray Dataset containing the data read from a file.
            locations:
                    A list of tuples containing the latitude and longitude of the locations for which data is requested.
            factors:
                    A list of strings representing the factors to be included in the dataset.

        Returns:
            An xarray Dataset containing only the data for the requested locations and factors.
        """
        # We start by filtering for locations
        latitudes = [location[0] for location in locations]
        longitudes = [location[1] for location in locations]
        location_trimmed_dataset = dataset.sel(latitude=latitudes, longitude=longitudes, method="nearest")

        # Then we filter for factors
        available_factors = set(dataset.data_vars.keys())
        factors_to_keep = [factor for factor in factors if factor in available_factors]
        factor_trimmed_dataset = location_trimmed_dataset[factors_to_keep]

        return factor_trimmed_dataset
