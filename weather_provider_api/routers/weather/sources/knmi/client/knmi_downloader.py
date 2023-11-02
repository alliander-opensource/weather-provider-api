# !/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
""" Module that holds the KNMI Downloader class
"""

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Union

import requests
from loguru import logger


class KNMIDownloader:
    """This class is based on the access methods used for the example downloads for the KNMI Data Platform.

    Due to the rather unusual method of file acquisition, changes were made to make sure only the intended files get
     downloaded and returned.
    """

    API_URL = os.environ.get("KNMI_API_URL", None)
    API_KEY = os.environ.get("KNMI_API_KEY", None)

    def __init__(
        self,
        dataset_name: str,
        dataset_version: str,
        temporary_download_folder: str = None,
        clear_files_from_folder: bool = False,
    ):
        self.dataset_name = dataset_name
        self.dataset_version = dataset_version

        self.temporary_download_folder = self._get_valid_temporary_folder(
            temporary_download_folder, clear_files_from_folder
        )
        logger.info("KNMIDownloader initialized.")
        logger.info(f"Dataset: [{self.dataset_name}] | Version: [{self.dataset_version}]")
        logger.info(f"Storing files in: [{self.temporary_download_folder}]")

    def validate_knmi_download_settings(self):
        if self.API_URL is None:
            raise ValueError("The KNMI Downloader is missing a KNMI API url!")
        if self.API_KEY is None:
            raise ValueError("The KNMI Downloader is missing an access key!")
        logger.info("KNMI download settings validation access test:")
        self.get_all_available_files()
        logger.info("KNMI download settings validated")

    @staticmethod
    def _get_valid_temporary_folder(temporary_download_folder: Union[str, None], clear_files_from_folder: bool):
        """A function that selects the folder for the KNMIDownloader to use to download files.

        Note that this is a temporary folder, and that

        Args:
            temporary_download_folder:  The folder to download to. If None was passed, the default temporary folder
                                         will be used
            clear_files_from_folder:    A boolean holding if the directory should be emptied if it contains files
                                         (True) or if the existence of files should raise an exception (False).

        Returns:
            An existing pathlib Path holding the (empty) folder to use for downloads

        Raises:
            ...:

        """
        if temporary_download_folder is None:
            # if no folder was given, return the OS's default temp dir
            return Path(tempfile.gettempdir())

        possible_download_folder = Path(temporary_download_folder)
        if not possible_download_folder.exists():
            # if the folder doesn't exist yet, we just create it.
            try:
                possible_download_folder.mkdir(parents=False, exist_ok=False)
                return possible_download_folder
            except FileNotFoundError as fnf_error:
                # The parent folder needs to exist
                raise FileNotFoundError(
                    f"The supplied download folder for KNMIDownloader was invalid. "
                    f"At least the parent folder needs to exist for: "
                    f"[{possible_download_folder}]"
                ) from fnf_error
            except FileExistsError as unknown_exception:
                # File didn't exist before, but does now (shouldn't happen)
                raise FileExistsError(
                    f"Inconsistency error when creating the download folder for KNMIDownloader: "
                    f"Initial check stated the target did not exist, but mkdir states it did!"
                    f" Original error: {unknown_exception}"
                ) from unknown_exception

        if not possible_download_folder.is_dir():
            raise FileExistsError(
                "The given target folder name for KNMIDownloader already existed, but as a file! "
                "The target folder is as such not available for use!"
            )

        if next(possible_download_folder.iterdir(), None) is not None and not clear_files_from_folder:
            # Folder is not empty, and we're not allowed to clear it
            raise FileExistsError(
                "Files exist within the target directory for KNMIDownloader, but file deletion is "
                "not allowed. The target folder can as such not be used!"
            )

        if next(possible_download_folder.iterdir(), None) is not None and clear_files_from_folder:
            # Folder is not empty, but we're allowed to clear it.
            try:
                shutil.rmtree(possible_download_folder)  # Clear everything within the folder
                possible_download_folder.mkdir(parents=False, exist_ok=False)
            except Exception as unknown_exception:
                logger.error("An unexpected Exception occurred while clearing the target directory for KNMIDownloader:")
                raise unknown_exception

        return possible_download_folder

    def get_all_available_files(self) -> list:
        """Requests a list with all available files for the configured dataset.

        Returns:
            A list of strings holding the possible files to request for the configured dataset.

        Notes:
            Depending on the dataset configured, this list may hold quite a large number of files.

        """
        logger.info(
            f"Fetching the full list of files available for dataset [{self.dataset_name}], "
            f"version [{self.dataset_version}]."
        )
        files_in_dataset = requests.get(
            f"{self.API_URL}/datasets/{self.dataset_name}/versions/{self.dataset_version}/files",
            headers={"Authorization": self.API_KEY},
            params={"maxKeys": 500},
            timeout=120,  # two minutes of waiting should be far more than enough for file retrieval
        )
        files_in_dataset = files_in_dataset.json()  # Reformat as JSON for proper access

        return files_in_dataset["files"]  # return only the list of file dictionaries

    def download_specific_file(self, filename: str, filesize: int):
        """Downloads a specific file to the set temporary download folder.

        Args:
            filename: The filename of the file to download
            filesize: The size of the file to download (used to validate the file)

        Returns:
            Nothing

        """
        logger.info(f"KNMIDownloader is starting the download of [{filename}], size [{filesize} bytes]")

        if (
            self.temporary_download_folder.joinpath(filename).exists()
            and self.temporary_download_folder.joinpath(filename).stat().st_size == filesize
        ):
            # A file with the correct size and name already exists. There is no need to re-download it.
            logger.info(f"File [{filename}] already exist. Skipping download.")
            return

        file_request = requests.get(
            f"{self.API_URL}/datasets/{self.dataset_name}/versions/{self.dataset_version}/files/{filename}/url",
            headers={"Authorization": self.API_KEY},
            timeout=120,  # 2 minutes to fetch a download url should be more than enough
        )

        temporary_download_url = file_request.json().get("temporaryDownloadUrl")
        logger.debug(f"Temporary download url for [{filename}] set to: {temporary_download_url}")

        self._download_and_save_file_by_name_and_size(temporary_download_url, filesize)

    def _download_and_save_file_by_name_and_size(self, temporary_download_url: str, filesize: int):
        downloaded_file = requests.get(temporary_download_url, timeout=10 * 60)  # 10 minutes should be enough
        file_name_of_download = str(
            re.findall("filename=(.+)", downloaded_file.headers["content-disposition"])[0]
        ).strip('"')

        # Saving the file:
        try:
            downloaded_file.raise_for_status()
            total_bytes_transferred = 0

            with open(self.temporary_download_folder.joinpath(file_name_of_download), "wb") as file_download:
                for chunk in downloaded_file.iter_content(chunk_size=1024 * 1024 * 20):  # 20Mb chunk size
                    if chunk:
                        file_download.write(chunk)
                        total_bytes_transferred += len(chunk)
        finally:
            logger.debug(f"File download complete: [{self.temporary_download_folder.joinpath(file_name_of_download)}]")

        if total_bytes_transferred != filesize:
            raise EOFError(
                f"The downloaded file for [{file_name_of_download}] did not match the expected file size:"
                f" {filesize} bytes"
            )
