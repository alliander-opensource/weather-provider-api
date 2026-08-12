# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""A module aimed at interfacing with the KNMI Data Platform, and downloading files from it.

This module is loosely based on the guides and examples provided by the KNMI Data Platform.
"""
import os
import re
import tempfile
from datetime import datetime, UTC, timedelta
from pathlib import Path

import requests
from loguru import logger


_MAX_ALLOWED_FILES_PER_REQUEST = 1000
_MAX_ALLOWED_FILES_PER_UPDATE_RUN = 2000

class KNMIDataPlatFormDownloadClient:
    """A client for downloading data from the KNMI Data Platform.

    This client is designed to handle the downloading of files from the KNMI Data Platform, ensuring that the number
    of files requested does not exceed the maximum allowed limit. It provides methods to download files based on
    specific parameters and handles the necessary authentication and request formatting.
    """

    def __init__(self) -> None:
        """Initialize the KNMIDataPlatFormDownloadClient."""
        self.data_platform_url = os.environ.get("KNMI_DATA_PLATFORM_URL", "https://api.dataplatform.knmi.nl/open-data")
        data_platform_key = os.environ.get("KNMI_DATA_PLATFORM_KEY", None)
        self.data_platform_quota_timeout: datetime = datetime.now(tz=UTC)

        if data_platform_key is None:
            raise ValueError(
                "The KNMI Data Platform Downloader is missing an access key! "
                "Please set the environment variable KNMI_DATA_PLATFORM_KEY to a valid access key."
            )
        self.data_platform_key = data_platform_key

        self._validate_access_settings()

        self.download_folder = self._validate_download_folder(
            os.environ.get("KNMI_DATA_PLATFORM_DOWNLOAD_FOLDER", None)
        )

        logger.info("KNMIDataPlatformDownloader initialized.")

    @property
    def on_quota_timeout(self) -> bool:
        """Check if the client is currently in a quota timeout state."""
        return datetime.now(tz=UTC) < self.data_platform_quota_timeout

    @property
    def request_headers(self) -> dict[str, str | bytes] | None:
        """Get the request headers for the KNMI Data Platform API requests."""
        request_headers: dict[str, str | bytes] | None = {
            "Authorization": f"Bearer {self.data_platform_key}"
        }
        return request_headers

    def get_dataplatform_access_url(self, dataset_name: str, dataset_version: str) -> str:
        """Get the access URL for the KNMI Data Platform."""
        return f"{self.data_platform_url}/v1/datasets/{dataset_name}/versions/{dataset_version}/files"


    def retrieve_file_and_size_list_for_dataset(
            self, dataset_name: str, dataset_version: str, max_files: int | None = None
    ) -> list[dict[str, str | int]] | None:
        # Make sure we're not currently in a quota timeout state
        if self.on_quota_timeout:
            logger.warning(
                "Quota timeout in effect. Cannot retrieve file list for dataset {} version {} until {}.",
                dataset_name,
                dataset_version,
                self.data_platform_quota_timeout,
            )
            return None

        max_keys = (
            min(max_files, _MAX_ALLOWED_FILES_PER_REQUEST) if max_files is not None else _MAX_ALLOWED_FILES_PER_REQUEST
        )
        next_page_token = None
        file_list: list[dict[str, str | int]] = []

        logger.debug(
            "Retrieving file list for dataset {} version {} with max keys {}.",
            dataset_name, dataset_version, max_keys
        )
        request_access_url = self.get_dataplatform_access_url(dataset_name, dataset_version)

        page: int = 1
        while True:
            logger.debug(
                "Requesting page {} of file list for dataset {} version {}.",
                page, dataset_name, dataset_version
            )
            request_params: dict[str, str | int | None] = {
                "orderBy": "created",
                "maxKeys": max_keys,
                "sorting": "desc",
                "nextPageToken": next_page_token,
            }
            response = requests.get(request_access_url, params=request_params, headers=self.request_headers, timeout=10)

            if response.status_code != 200:
                self._process_irregular_response(response)
                return None

            file_list.extend(response.json().get("files", []))
            if len(file_list) >= _MAX_ALLOWED_FILES_PER_UPDATE_RUN:
                logger.debug(
                    "Reached maximum allowed files per update run ({}). Stopping retrieval of file list.",
                    _MAX_ALLOWED_FILES_PER_UPDATE_RUN
                )
                file_list = file_list[:_MAX_ALLOWED_FILES_PER_UPDATE_RUN]  # Trim the list to the max_files limit
                break

            next_page_token = response.json().get("nextPageToken", None)
            if next_page_token is None:
                logger.debug("No next page token found in the response, assuming this is the last page of results.")
                break

            page += 1

        logger.info(f"Successfully retrieved file list from the KNMI Data Platform API. ({len(file_list)} files)")
        return file_list


    def _validate_access_settings(self) -> None:
        """Validate the access settings for the KNMI Data Platform."""

        # Check if the access key and URL are set at all
        if not self.data_platform_key:
            raise ValueError("KDP Access Error: access key is not set.")
        if not self.data_platform_url:
            raise ValueError("KDP Access Error: URL is not set.")

        # Check if the access key can be used to access the KNMI Data Platform
        ...

        logger.info("Access settings validated successfully.")

    @staticmethod
    def _validate_download_folder(download_folder: str | None) -> Path:
        """Validate the download folder for the KNMI Data Platform Downloader, ensuring it exists and is writable."""
        validated_download_folder : Path

        if download_folder is None:
            # Set a temporary default download folder if none is provided
            validated_download_folder = Path(tempfile.gettempdir()) / "knmi_data_platform_downloads"
            logger.warning("No download folder specified. Using temporary folder: {}", validated_download_folder)
        else:
            validated_download_folder = Path(download_folder)

        # Ensure the download folder exists
        if not validated_download_folder.exists():
            logger.warning("Download folder does not exist. Creating: {}", validated_download_folder)
            try:
                validated_download_folder.mkdir(parents=True, exist_ok=True)
            except FileNotFoundError as e:
                raise ValueError(f"Failed to create download folder: {validated_download_folder}. Error: {e}")
            except PermissionError as e:
                raise ValueError(f"Permission denied when creating download folder: {validated_download_folder}. Error: {e}")
            except Exception as e:
                raise ValueError(f"Unexpected error when creating download folder: {validated_download_folder}. Error: {e}")
        else:
            if not validated_download_folder.is_dir():
                raise ValueError(f"Download folder already exists but is not a directory: {validated_download_folder}")

        return validated_download_folder


    def _process_irregular_response(self, response: requests.Response) -> None:
        """Process irregular response from the KNMI Data Platform API."""
        match response.status_code:
            case 429:
                # Quota exceeded, set the quota timeout
                retry_after = int(response.headers.get("Retry-After", 3600))  # Default to 3600 seconds (1 hour)
                self.data_platform_quota_timeout = datetime.now(tz=UTC) + timedelta(seconds=retry_after)
                logger.warning(
                    "Quota exceeded. Entering quota timeout until {}. Retry after {} seconds.",
                    self.data_platform_quota_timeout,
                    retry_after,
                )
            case 403:
                logger.error(
                    "Access forbidden. Check your access key and permissions. Response: {}",
                    response.text,
                )
            case 404:
                logger.error(
                    "Resource not found. Check the requested URL and parameters. Response: {}",
                    response.text,
                )
            case 500:
                logger.error(
                    "Internal server error at KNMI Data Platform. Response: {}",
                    response.text,
                )
            case _:
                logger.error(
                    "Unexpected response from KNMI Data Platform. Status code: {}, Response: {}",
                    response.status_code,
                    response.text,
                )
                raise ValueError(
                    f"Unexpected response from KNMI Data Platform. Status code: {response.status_code}, "
                    f"Response: {response.text}"
                )

    def retrieve_download_information_for_file(
            self, file_name: str, dataset_name: str, dataset_version: str
    ) -> tuple[str, str | None] | None:
        # Make sure we're not currently in a quota timeout state
        if self.on_quota_timeout:
            logger.warning(
                "Quota timeout in effect. Cannot retrieve download information for file {} in dataset {} version {} until {}.",
                file_name,
                dataset_name,
                dataset_version,
                self.data_platform_quota_timeout,
            )
            return None
        # Make a request to the KNMI Data Platform to get the download information for the specified file
        file_information_url = self.get_dataplatform_access_url(dataset_name, dataset_version) + f"/{file_name}/url"
        response = requests.get(file_information_url, headers=self.request_headers, timeout=10)

        # Check the response status code and handle accordingly
        if response.status_code != 200:
            self._process_irregular_response(response)
            return None

        # Extract the temporary download URL and deprecation message from the response
        download_url: str | None = response.json().get("temporaryDownloadUrl", None)
        deprecation_message: str | None = response.headers.get("X-KNMI-Deprecation")

        if download_url is None:
            raise ValueError(
                f"Failed to retrieve download URL for file [{file_name}] from the KNMI Data Platform API. Response did not contain a temporaryDownloadUrl. Response: {response.text}"
            )

        return download_url, deprecation_message

    def retrieve_file(self, file_name: str, file_size: int, download_url: str) -> Path | None:
        """Retrieve a specific file from the KNMI Data Platform, and save it to the download folder.

        Args:
            file_name: The name of the file to retrieve.
            file_size: The expected size of the file to retrieve, used for validation.
            download_url: The temporary download URL for the file to retrieve.
        """
        if self.on_quota_timeout:
            logger.warning(
                "Quota timeout in effect. Cannot download file {} until {}.",
                file_name,
                self.data_platform_quota_timeout,
            )
            return None

        logger.info(f"Starting download of file [{file_name}] from the KNMI Data Platform.")

        # First we check if the file already exists in the download folder, and if it does, we check if the size matches the expected size.
        if (
            self.download_folder.joinpath(file_name).exists()
            and self.download_folder.joinpath(file_name).stat().st_size == file_size
        ):
            logger.info(
                f"File [{file_name}] already exists in the download folder with the expected size. Skipping download and returning existing file."
            )
            return self.download_folder.joinpath(file_name)

        self._download_and_save_file_by_name_and_size(download_url, file_name, file_size)

        return self.download_folder.joinpath(file_name)

    def _download_and_save_file_by_name_and_size(
        self, temporary_download_url: str, file_name: str, file_size: int
    ) -> None:
        """Download a file from the given temporary download URL.

        Downloads a file from the given temporary download URL, and saves it to the download folder with the given
        filename, validating the filesize.

        Args:
            temporary_download_url: The temporary download URL to download the file from.
            file_name: The name to save the downloaded file as.
            file_size: The expected size of the file, used for validation.
        """
        logger.info(f"Starting download of file [{file_name}] from temporary URL.")

        response = requests.get(temporary_download_url, timeout=10)

        if response.status_code != 200:
            self._process_irregular_response(response)

        filename_of_download = str(re.findall("filename=(.+)", response.headers["content-disposition"])[0]).strip('"')

        # Saving the file:
        try:
            response.raise_for_status()
            total_bytes_transferred = 0

            with open(self.download_folder.joinpath(filename_of_download), "wb") as file_download:
                for chunk in response.iter_content(chunk_size=1024 * 1024 * 20):  # 20Mb chunk size
                    if chunk:
                        file_download.write(chunk)
                        total_bytes_transferred += len(chunk)
        finally:
            logger.debug(f"File download complete: [{self.download_folder.joinpath(filename_of_download)}]")

        if total_bytes_transferred != file_size:
            raise EOFError(
                f"The downloaded file for [{file_name}] did not match the expected file size: {file_size} bytes. "
                f"Actual size: {total_bytes_transferred} bytes."
            )
        logger.info(f"File [{file_name}] downloaded and saved successfully with the expected file size.")

