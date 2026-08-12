# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Weather repository module."""

import re
import shutil
from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path

import xarray as xr
from loguru import logger
from pydantic import BaseModel

from weather_provider_api.config import APP_STORAGE_FOLDER
from weather_provider_api.routers.weather.utils.date_helpers import strftime_to_regex


class RepoUpdateResult(StrEnum):
    """Enum representing the result of a repository update."""

    SUCCESS = "Update successful"
    PARTIAL_SUCCESS = "Update partially successful"
    FAILURE = "Update failed"
    TIMEOUT = "Update timed out"


class RepoDataFetchResult(StrEnum):
    """Enum representing the result of a repository data fetch operation."""

    SUCCESS = "Data fetch successful"
    PARTIAL_SUCCESS = "Data fetch partially successful"
    FAILURE = "Data fetch failed"
    NO_DATA_AVAILABLE = "No data available for the specified parameters"


class WeatherRepositoryConfiguration(BaseModel):
    """Configuration for the weather repository.

    Args:
        identifier (str):
                Unique identifier for the repository.
        storage_path (Path):
                Path where the weather data will be stored.
        storage_states (set[str], optional):
                Set of states for which data should be stored. Defaults to an empty set.
        maximum_runtime_seconds (float, optional):
                Maximum allowed runtime for repository updates in seconds. Defaults to 2 hours.
        temporal_file_identifier (str, optional):
                Format string for temporal file identifiers. Defaults to "%Y%m%d_%H%M%S".
        affiliated_source_and_model (tuple[str, str]):
                Tuple containing the source and model name affiliated with this repository.
        netcdf_time_encoding (str, optional):
                Time encoding format for NetCDF files. Defaults to "hours since 2018-01-01 00:00:00".
    """

    identifier: str
    storage_path: Path
    storage_states: set[str] = set()
    maximum_runtime_seconds: float = 60 * 60 * 2  # Default: 2 hours
    temporal_file_identifier: str = "%Y%m%d%H"
    affiliated_source_and_model: tuple[str, str]
    netcdf_time_encoding: str = "hours since 2018-01-01 00:00:00"


class WeatherRepositoryBase(ABC):
    """Base class for weather repositories."""

    def __init__(self, config: WeatherRepositoryConfiguration):
        """Initialize the repository."""
        self.config = config
        # Attach the default storage states to the configuration if not already set
        self.config.storage_states.update(["raw", "processed"])

        # Make sure the storage path exists
        absolute_storage_path = self.absolute_storage_path
        if not absolute_storage_path.exists():
            absolute_storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created storage directory at: {absolute_storage_path}")

    @property
    def metadata(self) -> str:
        """Get the metadata of the repository."""
        return (
            f"Repository Identifier: {self.identifier}\n"
            f"Storage Path: {self.storage_path}\n"
            f"Storage States: {', '.join(self.config.storage_states)}\n"
            f"Maximum Runtime (seconds): {self.config.maximum_runtime_seconds}\n"
            f"Temporal File Identifier: {self.config.temporal_file_identifier}\n"
            f"Affiliated Source and Model: {self.source_and_model['source']} (( {self.source_and_model['model']} ))\n"
            f"NetCDF Time Encoding: {self.config.netcdf_time_encoding}"
        )

    @property
    def identifier(self) -> str:
        """Get the unique identifier for the repository."""
        return self.config.identifier

    @property
    def storage_path(self) -> Path:
        """Get the path where the weather data will be stored."""
        return self.config.storage_path

    @property
    def absolute_storage_path(self) -> Path:
        """Get the absolute path where the weather data will be stored."""
        return APP_STORAGE_FOLDER / self.storage_path

    @property
    def source_and_model(self) -> dict[str, str]:
        """Get the source and model name affiliated with this repository."""
        return {
            "source": self.config.affiliated_source_and_model[0],
            "model": self.config.affiliated_source_and_model[1],
        }

    @property
    def oldest_date_available(self) -> date:
        """Get the oldest date for which weather data is available in the repository."""
        raise NotImplementedError("Subclasses must implement the oldest_date_available property.")

    @property
    def newest_date_available(self) -> date:
        """Get the newest date for which weather data is available in the repository."""
        raise NotImplementedError("Subclasses must implement the newest_date_available property.")

    @abstractmethod
    def update(self, *, run_in_testmode: bool = False) -> tuple[RepoUpdateResult, str]:
        """Update the repository with new weather data up to the specified date.

        Args:
            run_in_testmode (bool, optional): Whether to run the update in test mode. Defaults to False.

        Returns:
            RepoUpdateResult:
                    The result of the update operation.
            str:
                    An optional message providing additional information about the update result.
        """
        raise NotImplementedError("Subclasses must implement the update method.")

    @abstractmethod
    def cleanup_storage(self) -> RepoUpdateResult:
        """Clean up the storage by removing outdated or unnecessary data.

        Returns:
            RepoUpdateResult:
                    The result of the cleanup operation.
        """
        raise NotImplementedError("Subclasses must implement the cleanup_storage method.")

    @abstractmethod
    def retrieve_data(
        self, from_date: date, to_date: date, locations: list[tuple[float, float]], factors: list[str]
    ) -> tuple[xr.Dataset | None, RepoDataFetchResult]:
        """Retrieve weather data for the specified date range.

        Args:
            from_date (date):
                    The start date of the data retrieval range.
            to_date (date):
                    The end date of the data retrieval range.
            locations (list[tuple[float, float]]):
                    A list of WGS84 location coordinates (latitude, longitude) for which to retrieve weather data.
            factors (list[str]):
                    A list of weather factors to retrieve (e.g., temperature, precipitation).

        Returns:
            xr.Dataset | None:
                    The retrieved weather data as an xarray Dataset, or None if no data is available.
            RepoDataFetchResult:
                    The result of the data fetch operation, indicating success, partial success, failure,
                    or no data available.
        """
        raise NotImplementedError("Subclasses must implement the retrieve_data method.")

    def purge_repository(self, identifier: str) -> RepoUpdateResult:
        """Permanently delete all data from the repository.

        Args:
            identifier (str):
                    The unique identifier of the repository to be purged.

        Returns:
            RepoUpdateResult:
                    The result of the purge operation.
        """
        # Verify that the provided identifier matches the repository's identifier to prevent accidental purging of the wrong repository
        if identifier != self.identifier:
            logger.error(
                f"Identifier mismatch: provided '{identifier}' does not match repository identifier "
                f"'{self.identifier}'. Purge operation aborted."
            )
            return RepoUpdateResult.FAILURE  # Identifier mismatch, purge operation failed

        # Proceed with the purge operation if the identifier matches
        try:
            # Implement the logic to permanently delete all data from the repository
            # This is a placeholder implementation and should be replaced with actual deletion logic
            logger.info(f"Purging repository '{self.identifier}' at path '{self.storage_path}'...")
            shutil.rmtree(self.storage_path)  # Remove the entire storage directory and its contents
            logger.info(f"Repository '{self.identifier}' purged successfully.")
            return RepoUpdateResult.SUCCESS
        except FileNotFoundError:
            logger.warning(f"Repository '{self.identifier}' not found at path '{self.storage_path}'. Nothing to purge.")
            return RepoUpdateResult.SUCCESS  # Consider it a success if the repository is already absent
        except PermissionError as e:
            logger.error(f"Permission error while purging repository '{self.identifier}': {e}")
            return RepoUpdateResult.FAILURE  # Permission error, purge operation failed
        except OSError as e:
            logger.error(f"OS error while purging repository '{self.identifier}': {e}")
            return RepoUpdateResult.FAILURE  # OS error, purge operation failed

    @classmethod
    def safely_delete_file(cls, file_path: Path) -> bool:
        """Safely delete a file from the repository storage.

        Args:
            file_path (Path): The path of the file to be deleted.

        Returns:
            bool: True if the file was successfully deleted, False otherwise.
        """
        try:
            if file_path.is_file():
                file_path.unlink()  # Delete the file
                logger.info(f"File '{file_path}' deleted successfully.")
                return True

            logger.warning(f"File '{file_path}' does not exist or is not a regular file. Deletion skipped.")
            return False  # File does not exist or is not a regular file
        except PermissionError as e:
            logger.error(f"Permission error while deleting file '{file_path}': {e}")
            return False  # Permission error, deletion failed
        except OSError as e:
            logger.error(f"OS error while deleting file '{file_path}': {e}")
            return False  # OS error, deletion failed

    def _retrieve_files_matching_period(self, from_date: date, to_date: date) -> list[Path]:
        """Helper method to retrieve files from the storage that match the specified date range.

        Args:
            from_date (date): The start date of the period for which to retrieve files.
            to_date (date): The end date of the period for which to retrieve files.

        Returns:
            list[Path]: A list of file paths that match the specified date range.
        """
        # Implement the logic to retrieve files from the storage that match the specified date range
        # This is a placeholder implementation and should be replaced with actual file retrieval logic
        matching_files: list[Path] = []
        for file in self.storage_path.glob("*.nc"):  # Assuming NetCDF files with .nc extension
            # Extract the date from the filename using the temporal_file_identifier format
            try:
                # Calculate the length of the prefix in the filename
                len_of_stem_prefix = (
                    len(self.config.affiliated_source_and_model[0])
                    + 1
                    + len(self.config.affiliated_source_and_model[1])
                    + 1
                )
                file_date_str = file.stem[len_of_stem_prefix:]  # Get the filename without the prefix
                file_date: date = datetime.strptime(file_date_str, self.config.temporal_file_identifier).date()

                logger.exception(
                    f"Checking file '{file}' with extracted date '{file_date}' against period from {from_date} to {to_date}."
                )
                if from_date <= file_date <= to_date:
                    matching_files.append(file)
            except ValueError:
                logger.warning(f"Filename '{file.name}' does not match the expected date format. Skipping file.")
                continue  # Skip files that do not match the expected date format

        logger.info(f"Found {len(matching_files)} files matching the period from {from_date} to {to_date}.")
        return matching_files

    @classmethod
    def _filter_dataset(
        cls, dataset: xr.Dataset, locations: list[tuple[float, float]], factors: list[str]
    ) -> xr.Dataset:
        """Helper method to filter the retrieved dataset based on the specified weather factors.

        Args:
            dataset (xr.Dataset):
                    The dataset to be filtered.
            locations (list[tuple[float, float]]):
                    A list of WGS84 location coordinates (latitude, longitude) to filter the dataset by.
            factors (list[str]):
                    A list of weather factors to retain in the dataset.

        Returns:
            xr.Dataset:
                    The filtered dataset containing only the specified weather factors.
        """
        # Select only the specified factors from the dataset
        factor_filtered_dataset = dataset[factors]  # Select only the specified factors from the dataset
        logger.info(f"Filtered dataset to include only factors: {factors}.")

        # Filter the dataset based on the specified locations
        filtered_dataset: xr.Dataset | None = None
        for location in locations:
            lat, lon = location

            if not filtered_dataset:
                # For the first location, initialize the filtered dataset
                filtered_dataset = factor_filtered_dataset.sel(latitude=lat, longitude=lon, method="nearest")
            else:
                filtered_dataset = xr.concat(
                    [filtered_dataset, factor_filtered_dataset.sel(latitude=lat, longitude=lon, method="nearest")],
                    dim="location",
                )
            logger.info(f"Filtered dataset to include data for location: (latitude={lat}, longitude={lon}).")

        if not filtered_dataset:
            logger.warning("No data available for the specified locations. Returning an empty dataset.")
            filtered_dataset = (
                xr.Dataset()
            )  # Return an empty dataset if no data is available for the specified locations

        return filtered_dataset

    def _extract_datetime_tag_from_file_name(self, file_name: str) -> str | None:
        """Extract a datetime tag from the file name if it matches the expected format.

        By transforming the temporal_file_identifier format string into a regular expression,
        this method checks if the file name contains a valid datetime tag and extracts it if present.

        Arguments:
            file_name:
                    The name of the file from which to extract the datetime tag.

        Returns:
            str | None:
                    The extracted datetime tag if it is present in the file name, None otherwise.
        """
        regex_pattern = strftime_to_regex(self.config.temporal_file_identifier)
        match = re.search(regex_pattern, file_name)
        if match:
            return match.group(0)

        logger.warning(f"File [{file_name}] does not contain a valid datetime tag.")
        return None
