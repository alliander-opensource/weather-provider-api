#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""A module aimed at interfacing with the KNMI Data Platform, and downloading files from it.

This module is loosely based on the guides and examples provided by the KNMI Data Platform.
"""

import os
import re
import tempfile
from pathlib import Path

import requests  # type: ignore
from loguru import logger

_MAX_ALLOWED_FILES_PER_REQUEST = 1000


class KNMIDataPlatformDownloader:
    """A class that can be used to download files from the KNMI Data Platform.

    This class is based on the access methods used for the example downloads for the KNMI Data Platform, but has
     been modified to make sure only the intended files get downloaded and returned.
    """

    def __init__(self) -> None:
        """Initialize the KNMIDataPlatformDownloader."""
        self.data_platform_url = os.environ.get("KNMI_DATA_PLATFORM_URL", "https://api.dataplatform.knmi.nl/open-data")
        self.data_platform_key = os.environ.get("KNMI_DATA_PLATFORM_KEY", None)

        if self.data_platform_key is None:
            raise ValueError(
                "The KNMI Data Platform Downloader is missing an access key! "
                "Please set the environment variable KNMI_DATA_PLATFORM_KEY to a valid access key."
            )

        self._validate_data_platform_access_settings()

        self.download_folder = self._validate_download_folder(
            os.environ.get("KNMI_DATA_PLATFORM_DOWNLOAD_FOLDER", None)
        )

        logger.info("KNMIDataPlatformDownloader initialized.")

    def retrieve_file_and_size_list_for_dataset(
        self,
        dataset_name: str,
        dataset_version: str,
        max_files: int | None = None,
    ) -> list[dict[str, str | int]]:
        """Retrieve the list of files available for a given dataset and version from the KNMI Data Platform.

        Contacts the KNMI Data Platform API to retrieve the list of files available for the given dataset and version, and returns a list of file URLs to download.
        The number of files returned is limited by the max_files parameter. Because the KNMI Data Platform API allows a maximum of 1000 files to be retrieved in a single
        request, higher numbers will be handled via pagination.

        Args:
            dataset_name: The name of the dataset to retrieve the file list for.
            dataset_version: The version of the dataset to retrieve the file list for.
            max_files: The maximum number of files to retrieve from the file list. If None, all files will be retrieved.
        """
        max_keys = (
            min(max_files, _MAX_ALLOWED_FILES_PER_REQUEST) if max_files is not None else _MAX_ALLOWED_FILES_PER_REQUEST
        )
        next_page_token = None
        file_list: list[dict[str, str | int]] = []

        logger.debug(
            f"Retrieving file list for dataset [{dataset_name}] version [{dataset_version}] from the "
            f"KNMI Data Platform API with the following parameters: max_files={max_files}"
        )

        access_url = f"{self.data_platform_url}/v1/datasets/{dataset_name}/versions/{dataset_version}/files"
        headers = {"Authorization": self.data_platform_key}

        while True:
            params: dict[str, str | int | None] = {
                "orderBy": "created",
                "maxKeys": max_keys,
                "sorting": "desc",
                "nextPageToken": next_page_token,
            }
            response = requests.get(access_url, params=params, headers=headers, timeout=10)

            if response.status_code != 200:
                self._process_status_code_error(response.status_code, response.text)

            file_list.extend(response.json().get("files", []))
            if max_files is not None and len(file_list) >= max_files:
                logger.debug(
                    f"Retrieved the maximum number of files requested ({max_files}). Stopping file list retrieval."
                )
                file_list = file_list[:max_files]  # Trim the list to the max_files limit
                break

            next_page_token = response.json().get("nextPageToken", None)
            if next_page_token is None:
                logger.debug("No next page token found in the response, assuming this is the last page of results.")
                break

        logger.info(f"Successfully retrieved file list from the KNMI Data Platform API. ({len(file_list)} files)")
        return file_list

    def retrieve_download_information_for_file(
        self, file_name: str, dataset_name: str, dataset_version: str
    ) -> tuple[str, str | None]:
        """Retrieve relevant information for downloading a file from the KNMI Data Platform."""
        # First we build the file information retrieval url
        file_information_url = (
            f"{self.data_platform_url}/v1/datasets/{dataset_name}/versions/{dataset_version}/files/{file_name}/url"
        )

        # Then we make a request to the KNMI Data Platform API to retrieve the download URL and deprecation message (if applicable) for the file
        headers = {"Authorization": self.data_platform_key}
        response = requests.get(file_information_url, headers=headers, timeout=10)

        # Handle potential errors in the response
        if response.status_code != 200:
            self._process_status_code_error(response.status_code, response.text)

        download_url: str | None = response.json().get("temporaryDownloadUrl", None)
        deprecation_message: str | None = response.headers.get("X-KNMI-Deprecation")

        if download_url is None:
            raise ValueError(
                f"Failed to retrieve download URL for file [{file_name}] from the KNMI Data Platform API. Response did not contain a temporaryDownloadUrl. Response: {response.text}"
            )

        return download_url, deprecation_message

    def retrieve_file(self, file_name: str, file_size: int, download_url: str) -> Path:
        """Retrieve a specific file from the KNMI Data Platform, and save it to the download folder.

        Args:
            file_name: The name of the file to retrieve.
            file_size: The expected size of the file to retrieve, used for validation.
            download_url: The temporary download URL for the file to retrieve.
        """
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

    def _validate_data_platform_access_settings(self) -> None:
        """Validate the access settings for the KNMI Data Platform, by making a test request to the API."""
        try:
            self.retrieve_file_and_size_list_for_dataset(
                dataset_name="waarschuwingen_nederland_48h", dataset_version="1.0", max_files=1
            )
            logger.info("Successfully validated access settings for the KNMI Data Platform API.")
        except Exception as e:
            raise ValueError(f"Failed to validate access settings for the KNMI Data Platform API. Error: {e}") from e

    def _validate_download_folder(self, download_folder: str | None) -> Path:
        """Validate the download folder, and create it if it does not exist."""
        validated_folder: Path

        if download_folder is None:
            validated_folder = Path(tempfile.gettempdir()) / "knmi_data_platform_downloads"
            validated_folder.mkdir(parents=False, exist_ok=True)
            logger.warning(
                f"No download folder specified for the KNMI Data Platform Downloader, using temporary folder: [{validated_folder}]"
            )
            return validated_folder

        validated_folder = Path(download_folder)
        if validated_folder.exists():
            logger.info(
                f"Using specified existing download folder for the KNMI Data Platform Downloader: [{validated_folder}]"
            )
            return validated_folder

        try:
            validated_folder.mkdir(parents=False, exist_ok=False)
            logger.info(f"Created download folder for the KNMI Data Platform Downloader: [{validated_folder}]")
            logger.info(
                f"Using specified existing download folder for the KNMI Data Platform Downloader: [{validated_folder}]"
            )
            return validated_folder
        except FileNotFoundError as e:
            raise ValueError(
                f"The specified download folder for the KNMI Data Platform Downloader does not exist, and could not be created: [{validated_folder}]"
            ) from e
        except FileExistsError as e:
            raise ValueError(
                f"The specified download folder for the KNMI Data Platform Downloader already exists, but is not a directory: [{validated_folder}]"
            ) from e
        except Exception as e:
            raise ValueError(
                f"An error occurred while validating the specified download folder for the KNMI Data Platform Downloader: [{validated_folder}]. Error: {e}"
            ) from e

    def _process_status_code_error(self, status_code: int, response_text: str) -> None:
        """Process an error response from the KNMI Data Platform API, and raise a descriptive ValueError."""
        if status_code == 400:
            raise ValueError(f"Bad request to the KNMI Data Platform API. Response: {response_text}")
        elif status_code == 401:
            raise ValueError(
                f"Unauthorized access to the KNMI Data Platform API. Check your API key. Response: {response_text}"
            )
        elif status_code == 403:
            raise ValueError(
                f"Forbidden access to the KNMI Data Platform API. Check your permissions. Response: {response_text}"
            )
        elif status_code == 404:
            raise ValueError(
                f"Dataset or version not found in the KNMI Data Platform API. Check your dataset name and version. Response: {response_text}"
            )
        elif status_code == 500:
            raise ValueError(
                f"Internal server error in the KNMI Data Platform API. Try again later. Response: {response_text}"
            )
        else:
            raise ValueError(
                f"Unexpected error from the KNMI Data Platform API. Status code: {status_code}. Response: {response_text}"
            )

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
            self._process_status_code_error(response.status_code, response.text)

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
