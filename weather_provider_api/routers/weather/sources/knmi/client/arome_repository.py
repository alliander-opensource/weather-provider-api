#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import re
from datetime import UTC, date, datetime
from enum import StrEnum
from importlib.util import find_spec
from pathlib import Path

import xarray as xr
from loguru import logger

from weather_provider_api.routers.weather.repository.repository import (
    RepoDataFetchResult,
    RepoUpdateResult,
    WeatherRepositoryBase,
    WeatherRepositoryConfiguration,
)
from weather_provider_api.routers.weather.sources.knmi.client.knmi_data_platform_downloader import (
    KNMIDataPlatformDownloader,
)
from weather_provider_api.routers.weather.sources.knmi.utils.knmi_arome_process_tar_file import (
    process_knmi_arome_cy43_p1_tar_file_into_netcdf,
)
from weather_provider_api.routers.weather.utils.date_helpers import strftime_to_regex, subtract_months


class AromeSuggestedFileHandling(StrEnum):
    """Enum representing the update status of a file in the repository."""

    LEAVE_AS_IS = "Leave the file as it is, no update needed"
    DEPRECATE = "Deprecate the existing file in the repository and download the new file to replace it"
    UPDATE_DEPRECATED = "Update the deprecated file in the repository"
    UPDATE = "Update the file in the repository"


class HarmonieAromeRepository(WeatherRepositoryBase):
    """Repository for the KNMI Harmonie Arome weather model."""

    def __init__(self):
        """Initialize the repository."""
        super().__init__(
            WeatherRepositoryConfiguration(
                identifier="KNMI Harmonie Arome",
                storage_path=Path("knmi/arome"),
                storage_states={"raw", "processed", "deprecated"},
                maximum_runtime_seconds=60 * 60 * 3,  # 3 hours
                temporal_file_identifier="%Y%m%d%H",
                affiliated_source_and_model=("knmi", "arome"),
            )
        )
        self.knmi_dataset_name = "harmonie_arome_cy43_p1"
        self.knmi_dataset_version = "1.0"
        self.knmi_data_platform_downloader = KNMIDataPlatformDownloader()
        logger.info(f"Initialized {self.__class__.__name__} with configuration:\n{self.metadata}")

    @property
    def oldest_date_available(self) -> date:
        """Return the oldest date for which data is available."""
        oldest_datetime = subtract_months(datetime.now(UTC).date(), 36)  # Three years back
        return oldest_datetime

    @property
    def newest_date_available(self) -> date:
        """Return the newest date for which data is available."""
        return date.today()

    def update(self, *, run_in_testmode: bool = False) -> tuple[RepoUpdateResult, str]:
        """Update the repository with new data."""
        msg = f"Updating {self.identifier} repository"
        if run_in_testmode:
            msg += " (test mode)"
        logger.info(msg)

        # Check if the cfgrib library is installed before attempting to read any GRIB files
        self._verify_cfgrib_installation()

        # Determine which files can be updated
        files_available_for_download: list[dict[str, str | int]] = self.get_files_available_for_download()

        # Get a list of the currently already downloaded files in the repository
        existing_files_in_repository = self.get_existing_files_in_repository()

        update_result, update_details = self._process_file_updates(
            available_files=files_available_for_download,
            existing_files=existing_files_in_repository,
            run_in_testmode=run_in_testmode,
        )

        return update_result, update_details

    def _verify_cfgrib_installation(self) -> None:
        """Verify that the cfgrib library is installed."""
        if find_spec("cfgrib") is None:
            error_msg = "The cfgrib library is required to read GRIB files. Please install it and verify it is working."
            logger.error(error_msg)
            raise ImportError(error_msg)

    def get_files_available_for_download(self) -> list[dict[str, str | int]]:
        """Determine which files could be updated via the KNMI Data Platform.

        Return:
            list[dict[str, str | int]]:
                    A list of dictionaries containing information about the files that can be updated,
                    including 'name' and 'size'.
        """
        # Placeholder implementation: In a real implementation, this would check the remote source for new files
        kdp_downloader = KNMIDataPlatformDownloader()

        # Retrieve the list of all available files for the relevant dataset and version from the KNMI Data Platform
        all_files_available_on_knmi_data_platform = kdp_downloader.retrieve_file_and_size_list_for_dataset(
            dataset_name=self.knmi_dataset_name,
            dataset_version=self.knmi_dataset_version,
        )

        # Filter the list of files to those that match the targeted download pattern
        filtered_file_list = self._filter_file_list_down_to_wanted_files(all_files_available_on_knmi_data_platform)

        return filtered_file_list

    def cleanup_storage(self) -> RepoUpdateResult:
        """Clean up the storage by removing or archiving old or deprecated files."""
        result = RepoUpdateResult.SUCCESS
        for file in self.get_existing_files_in_repository():
            file_path = Path(file["path"]) if isinstance(file["path"], str) else file["path"]
            datetime_tag = self._extract_datetime_tag_from_file_name(file_name=str(file["name"]))
            if datetime_tag is None:
                self.safely_delete_file(file_path=file_path)
                continue
            file_date = datetime.strptime(datetime_tag, self.config.temporal_file_identifier).date()
            if file_date < self.oldest_date_available or file_date > self.newest_date_available:
                if not self.safely_delete_file(file_path=file_path):
                    logger.error(f"Failed to delete file [{file_path}] that is outside the date range of interest.")
                    result = RepoUpdateResult.FAILURE
                elif result == RepoUpdateResult.SUCCESS:
                    result = RepoUpdateResult.PARTIAL_SUCCESS
        return result

    def retrieve_data(
        self, from_date: date, to_date: date, locations: list[tuple[float, float]], factors: list[str]
    ) -> tuple[xr.Dataset | None, RepoDataFetchResult]:
        """Retrieve data from the repository for the specified date range, locations, and factors."""
        # We start by determining which files in the repository match the specified date range
        required_files_for_data = self._retrieve_files_matching_period(from_date=from_date, to_date=to_date)

        # Then we check each file for the requested factors and locations, and read the data from the file if it
        # matches the request. If multiple files match the request, we combine the data from the files into a single
        # Dataset and return it.
        try:
            filtered_dataset = self._gather_data_from_files_and_combine_into_dataset(
                required_files_for_data, locations, factors
            )
        except Exception as e:
            logger.error(f"An error occurred while retrieving data from the repository: {e}")
            return None, RepoDataFetchResult.FAILURE

        return filtered_dataset, RepoDataFetchResult.SUCCESS

    def _filter_file_list_down_to_wanted_files(
        self, file_list: list[dict[str, str | int]]
    ) -> list[dict[str, str | int]]:
        """Filter the list of files to those that match the expected download pattern.

        Files only need to be downloaded when match the set time pattern (e.g., 00:00, 06:00, 12:00, 18:00) and are not
          already present in the repository. They also need to be within the date range of interest
          (between oldest_date_available and newest_date_available).

        Arguments:
            file_list:
                    A list of dictionaries containing file information, including 'name' and 'size'.

        Returns:
            A filtered list of dictionaries containing only the files that match the expected download pattern.

        """
        filtered_filed: list[dict[str, str | int]] = []

        for file in file_list:
            file_name: str = str(file["filename"])
            # First we verify that the file name contains a date and time in the expected format, and extract
            # the date and time from the file name
            try:
                filename_datetime_part = self._extract_datetime_tag_from_file_name(file_name=file_name)
                if not filename_datetime_part:
                    logger.error(f"File name [{file_name}] does not contain a valid datetime tag and will be skipped.")
                    continue
                file_datetime = datetime.strptime(filename_datetime_part, self.config.temporal_file_identifier)
            except ValueError:
                logger.debug(f"File [{file_name}] does not match the expected temporal pattern and will be skipped.")
                continue

            # Then we check if the file datetime is within the date range of interest
            if not self.oldest_date_available <= file_datetime.date() <= self.newest_date_available:
                logger.debug(f"File [{file_name}] is outside the date range of interest and will be skipped.")
                continue

            # Finally we check if the file_datetime matches the expected time pattern (e.g., 00:00, 06:00, 12:00, 18:00)
            if file_datetime.hour not in {0, 6, 12, 18}:
                continue

            # If the file passed all checks, we add it to the list of files to download
            filtered_filed.append(file)
        return filtered_filed

    def get_existing_files_in_repository(self) -> list[dict[str, str | Path]]:
        """Get a set of the currently already downloaded files in the repository.

        Returns:
            list[dict[str, str | Path]]:
                    A list of dictionaries containing information about the files that are already present in the
                    repository, including 'name', 'datetime_tag', 'state', and 'path'.

        """
        existing_files: list[dict[str, str | Path]] = []

        # List all files with .nc or .deprecated.nc suffixes
        all_files_in_storage_folder = list(self.absolute_storage_path.glob("*.nc")) + list(
            self.absolute_storage_path.glob("*.deprecated.nc")
        )

        for file in all_files_in_storage_folder:
            file_path = Path(file)
            file_name: str = file_path.name

            # Remove both suffixes if present
            if file_name.endswith(".deprecated.nc"):
                base_name = file_name[: -len(".deprecated.nc")]
                file_state = "deprecated"
            elif file_name.endswith(".raw.nc"):
                base_name = file_name[: -len(".raw.nc")]
                file_state = "raw"
            elif file_name.endswith(".nc"):
                base_name = file_name[: -len(".nc")]
                file_state = "processed"
            else:
                logger.warning(
                    f"File [{file_name}] in repository does not have a recognized suffix and will be skipped."
                )
                continue

            # Extract the datetime tag (YYYYMMDD_HH00) from the base name
            # The pattern is always preceded by an underscore and at the end of the base name
            match = re.search(strftime_to_regex(self.config.temporal_file_identifier), base_name)
            if match:
                datetime_tag = match.group(0)
            else:
                logger.warning(f"File [{file_name}] does not contain a valid datetime tag and will be skipped.")
                continue

            existing_files.append(
                {"name": base_name, "datetime_tag": datetime_tag, "state": file_state, "path": file_path}
            )

        return existing_files

    def _process_file_updates(
        self,
        available_files: list[dict[str, str | int]],
        existing_files: list[dict[str, str | Path]],
        run_in_testmode: bool,
    ) -> tuple[RepoUpdateResult, str]:
        """Process the file updates by determining which files need to be updated and performing the necessary updates.

        Arguments:
            available_files:
                    A list of dictionaries containing information about the files that can be updated,
                    including 'name' and 'size'.
            existing_files:
                    A list of dictionaries containing information about the files that are already present in the
                    repository, including 'name' and 'state'.
            run_in_testmode:
                    A boolean indicating whether the update is being run in test mode. If True, no actual downloading
                    or file operations will be performed.

        Returns:
            RepoUpdateResult:
                    An enum indicating the result of the update operation 
                    (e.g., SUCCESS, FAILURE, NO_UPDATES_AVAILABLE).
            str:
                    A message providing additional details about the update result.
        """
        update_result = RepoUpdateResult.SUCCESS
        update_message = "File updates processed successfully."
        processed_files_count = 0
        successfully_processed_files_count = 0

        # Step through each available file and determine if it needs to be (re-)downloaded and processed
        for file in available_files:
            datetime_tag_for_file = self._extract_datetime_tag_from_file_name(file_name=str(file["filename"]))

            existing_files_with_same_datetime_tag = [
                existing_file
                for existing_file in existing_files
                if existing_file["datetime_tag"] == datetime_tag_for_file
            ]

            file_update_result = self._process_file_update(file, existing_files_with_same_datetime_tag, run_in_testmode)

            processed_files_count += 1
            if file_update_result == RepoUpdateResult.SUCCESS:
                successfully_processed_files_count += 1
            elif file_update_result == RepoUpdateResult.FAILURE:
                logger.error(f"Failed to process file [{file['filename']}].")
                update_result = RepoUpdateResult.PARTIAL_SUCCESS

            if processed_files_count > 2 and successfully_processed_files_count / processed_files_count < 0.5:
                update_result = RepoUpdateResult.FAILURE
                update_message = (
                    "More than 50% of the available files could not be processed successfully, which "
                    "may indicate an issue with the update process. Please check the logs for more "
                    "details."
                )
                break

        if update_result == RepoUpdateResult.PARTIAL_SUCCESS:
            update_message = (
                f"Some files could not be processed successfully. {successfully_processed_files_count} "
                f"out of {processed_files_count} files were processed successfully. Please check the "
                "logs for more details."
            )

        return update_result, update_message

    def _process_file_update(
        self,
        file: dict[str, str | int],
        existing_files_with_same_datetime_tag: list[dict[str, str | Path]],
        run_in_testmode: bool,
    ) -> RepoUpdateResult:
        """Process a single file update by determining if it needs an update and performing the update operations.

        Arguments:
            file:
                    A dictionary containing information about the file that can be updated, including 'filename' and 'size'.
            existing_files_with_same_datetime_tag:
                    A list of dictionaries containing information about the files that are already present in the
                     repository and have the same datetime tag as the file being processed, including
                     'name' and 'state'.
            run_in_testmode:
                    A boolean indicating whether the update is being run in test mode. If True, no actual downloading
                     or file operations will be performed.

        Returns:
            RepoUpdateResult:
                    An enum indicating the result of the file update operation (e.g., SUCCESS, FAILURE).
        """
        # First we determine the suggested file handling action based on the existing files with the same datetime tag
        if run_in_testmode:
            logger.info(
                f"Test mode: Simulating processing of file [{file['name']}]. "
                "No actual download or file operations will be performed."
            )
            return RepoUpdateResult.SUCCESS

        suggested_file_handling = self._determine_suggested_file_handling(file, existing_files_with_same_datetime_tag)

        if suggested_file_handling == AromeSuggestedFileHandling.LEAVE_AS_IS:
            logger.info(f"File [{file['filename']}] is already present in the repository and does not require an update.")
            return RepoUpdateResult.SUCCESS

        if suggested_file_handling == AromeSuggestedFileHandling.DEPRECATE:
            # Rename the existing file to deprecate it
            for existing_file in existing_files_with_same_datetime_tag:
                if existing_file["state"] == "processed":
                    self._deprecate_existing_file(existing_file["path"])  # type: ignore
            return RepoUpdateResult.SUCCESS

        if suggested_file_handling in {AromeSuggestedFileHandling.UPDATE, AromeSuggestedFileHandling.UPDATE_DEPRECATED}:
            download_url, _ = self.knmi_data_platform_downloader.retrieve_download_information_for_file(
                dataset_name=self.knmi_dataset_name,
                dataset_version=self.knmi_dataset_version,
                file_name=str(file["filename"]),
            )
            tar_file: Path = self.knmi_data_platform_downloader.retrieve_file(
                file_name=str(file["filename"]),
                file_size=int(file["size"]),
                download_url=download_url,
            )

            try:
                process_knmi_arome_cy43_p1_tar_file_into_netcdf(
                    tar_file_path=tar_file,
                    target_netcdf_file_path=self.absolute_storage_path,
                    target_netcdf_file_name=f"{self.source_and_model['source']}_{self.source_and_model['model']}_{self._extract_datetime_tag_from_file_name(file_name=str(file['filename']))}.nc",
                    datetime_tag=str(self._extract_datetime_tag_from_file_name(file_name=str(file["filename"]))),
                )
            except Exception as e:
                logger.error(f"An error occurred while processing file [{file['filename']}]: {e}")
                return RepoUpdateResult.FAILURE

        return RepoUpdateResult.SUCCESS

    def _determine_suggested_file_handling(
        self, file: dict[str, str | int], existing_files_with_same_datetime_tag: list[dict[str, str | Path]]
    ) -> AromeSuggestedFileHandling:
        """Determine the suggested file handling action based on the existing files with the same datetime tag.

        Arguments:
            file:
                    A dictionary containing information about the file that can be updated, including 'name' and 'size'.
            existing_files_with_same_datetime_tag:
                    A list of dictionaries containing information about the files that are already present in the
                     repository and have the same datetime tag as the file being processed,
                     including 'name', 'state', and 'path'.

        Returns:
            AromeSuggestedFileHandling:
                    An enum indicating the suggested file handling action
                     (e.g., LEAVE_AS_IS, DEPRECATE, UPDATE_DEPRECATED, UPDATE).
        """
        if len(existing_files_with_same_datetime_tag) == 0:
            logger.info(
                f"No existing file with the same datetime tag as file [{file['filename']}] was found in the repository. "
                "The file can be downloaded and added to the repository without deprecating any existing files."
            )
            return AromeSuggestedFileHandling.UPDATE

        if len(existing_files_with_same_datetime_tag) != 1:
            logger.warning(
                f"Multiple existing files with the same datetime tag as file [{file['filename']}] were found in the "
                "repository. This is unexpected and may indicate an issue with the repository state. The file will "
                "be left as is to avoid potential data integrity issues, but the repository state should be "
                "investigated and cleaned up if necessary."
            )
            return AromeSuggestedFileHandling.LEAVE_AS_IS

        if existing_files_with_same_datetime_tag[0]["state"] == "deprecated":
            # An existing deprecated file with the same datetime tag is present, so if a new non-deprecated file with
            # the same datetime tag is available, we can update the deprecated file with the new file
            _, deprecation_message = self.knmi_data_platform_downloader.retrieve_download_information_for_file(
                dataset_name=self.knmi_dataset_name,
                dataset_version=self.knmi_dataset_version,
                file_name=str(file["filename"]),
            )
            if deprecation_message:
                logger.warning(
                    f"File [{file['filename']}] is available for download and can be used to update the existing "
                    f"deprecated file with the same datetime tag, but a deprecation message was found: "
                    f"{deprecation_message}. The file will be left as is to avoid potential data integrity issues, "
                    "but the deprecation message should be investigated to determine if the file can be updated or "
                    "if the deprecation message indicates an issue with the file."
                )
                return AromeSuggestedFileHandling.LEAVE_AS_IS
            logger.info(
                f"File [{file['filename']}] is available for download and can be used to update the existing deprecated "
                "file with the same datetime tag. The existing deprecated file will be updated with the new file."
            )
            return AromeSuggestedFileHandling.UPDATE_DEPRECATED

        if existing_files_with_same_datetime_tag[0]["state"] == "processed":
            # A processed file exists and can be left as is unless the file has since been labeled as deprecated.
            _, deprecation_message = self.knmi_data_platform_downloader.retrieve_download_information_for_file(
                dataset_name=self.knmi_dataset_name,
                dataset_version=self.knmi_dataset_version,
                file_name=str(file["filename"]),
            )
            if deprecation_message:
                logger.warning(
                    f"File [{file['filename']}] is available for download and has the same datetime tag as an existing "
                    f"processed file in the repository, but a deprecation message was found: {deprecation_message}. "
                    "The existing file will be deprecated."
                )
                return AromeSuggestedFileHandling.DEPRECATE

            logger.info(
                f"File [{file['filename']}] is available for download and has the same datetime tag as an existing "
                "processed file in the repository, but no deprecation message was found. The existing file will be "
                "left as is to avoid potential data integrity issues, but the file and its metadata should be "
                "investigated to determine if the file can be updated or if there are any issues with the file."
            )
            return AromeSuggestedFileHandling.LEAVE_AS_IS

        logger.warning(
            f"File [{file['filename']}] is available for download and has the same datetime tag as an existing file in "
            f"the repository with an unexpected state [{existing_files_with_same_datetime_tag[0]['state']}]. The "
            "file will be updated in an attempt to fix the repository state."
        )
        return AromeSuggestedFileHandling.UPDATE

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

        for file in required_files_for_data:
            try:
                dataset: xr.Dataset = xr.open_dataset(file, engine="netcdf4", mode="r")  # type: ignore
                filtered_dataset = self._filter_dataset_by_locations_and_factors(dataset, locations, factors)
                if combined_dataset is None:
                    combined_dataset = filtered_dataset
                else:
                    combined_dataset = xr.concat([combined_dataset, filtered_dataset], dim="time")
            except Exception as e:
                logger.error(f"An error occurred while reading file [{file}]: {e}")
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

    def _deprecate_existing_file(self, filename: Path) -> RepoUpdateResult:
        """Deprecate the existing file by renaming it with a .deprecated.nc suffix.

        Arguments:
            filename:
                    The name of the file to be deprecated.
        """
        existing_file_path = self.config.storage_path / filename
        deprecated_file_path = self.config.storage_path / f"{filename.stem}.deprecated{filename.suffix}"
        try:
            existing_file_path.rename(deprecated_file_path)
            logger.info(f"File [{existing_file_path}] has been deprecated and renamed to [{deprecated_file_path}].")
        except Exception as e:
            logger.error(f"An error occurred while deprecating file [{existing_file_path}]: {e}")
            return RepoUpdateResult.FAILURE

        return RepoUpdateResult.SUCCESS
