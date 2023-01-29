#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import requests
import structlog


class KNMIDownloader:
    """
    A class based on the new access methods for the new KNMI Data Platform.
    """

    def __init__(
            self,
            dataset_name: str,
            dataset_version: str,
            ignore_files_up_to: str,
            number_of_files: int,
            download_folder: Path
    ):
        self.api_url = os.environ.get("KNMI_API_URL")
        self.api_key = os.environ.get("KNMI_API_KEY")
        self.logger = structlog.get_logger(__name__)
        self.dataset_name = dataset_name
        self.dataset_version = dataset_version
        self.start_after_filename = ignore_files_up_to
        self.max_keys = number_of_files
        self.download_folder = download_folder

    def knmi_download_request(self):
        # A function that looks up the files to download (based on the ignore_files_up_to field), downloads those and
        # returns a list of downloaded files and the temporary directory to find them in.
        self.logger.debug(
            "Downloading file list for dataset ["
            + self.dataset_name
            + "], version ["
            + self.dataset_version
            + "].",
            datetime=datetime.utcnow(),
        )
        files_for_dataset = requests.get(
            f"{self.api_url}/datasets/{self.dataset_name}/versions/{self.dataset_version}"
            f"/files",
            headers={"Authorization": self.api_key},
            params={
                "maxKeys": self.max_keys,
                "startAfterFilename": self.start_after_filename,
            },
        )

        files_for_dataset = files_for_dataset.json()  # Reformat to JSON
        file_list = files_for_dataset.get("files")

        if self.download_folder.exists():
            shutil.rmtree(self.download_folder)  # Remove the folder (immediately cleaning it) if it already existed

        # Create a nice clean folder to use
        self.download_folder.mkdir()

        for file in file_list:
            self.knmi_download_file_to_temp(
                file, self.download_folder, self.dataset_name, self.dataset_version
            )

        return file_list

    def knmi_download_file_to_temp(
            self, file_data, file_storage_dir: Path, dataset_name: str, dataset_version: str
    ):
        # A function that downloads the requested files to a temporary folder and
        file_name = file_data.get("filename")
        file_size = file_data.get("size")

        self.logger.debug(
            "Initializing download of ["
            + file_name
            + "], expecting file size of ["
            + str(file_size)
            + "].",
            datetime=datetime.utcnow(),
        )

        if (
                Path(file_storage_dir).joinpath(file_name).exists()
                and Path(file_storage_dir).joinpath(file_name).stat().st_size == file_size
        ):
            # A file with the right size and name already exists. No need to download again
            self.logger.debug(
                "Usable file" + file_name + " was found in temporary directory. "
                                            "Skipping download",
                datetime=datetime.utcnow(),
            )
            return True

        file_request = requests.get(
            f"{self.api_url}/datasets/{dataset_name}/versions/{dataset_version}/files/{file_name}/url",
            headers={"Authorization": self.api_key},
        )

        temporary_download_url = file_request.json().get("temporaryDownloadUrl")
        self.logger.debug(
            "Acquired temporary download URL: [" + temporary_download_url + "].",
            datetime=datetime.utcnow(),
        )

        downloaded_file = requests.get(temporary_download_url)
        downloaded_file_name = str(
            re.findall("filename=(.+)", downloaded_file.headers["content-disposition"])[
                0
            ]
        ).strip('"')

        # Save the downloaded file
        try:
            downloaded_file.raise_for_status()
            total = 0

            with open(Path(file_storage_dir).joinpath(downloaded_file_name), "wb") as f:
                for chunk in downloaded_file.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
        finally:
            downloaded_file.close()
            self.logger.debug(
                "File downloaded to ["
                + str(Path(file_storage_dir).joinpath(downloaded_file_name))
                + "].",
                datetime=datetime.utcnow(),
            )

        self.logger.debug(
            "Downloaded file size approximated ["
            + str(total)
            + "]; expected file size was ["
            + str(file_size)
            + "].",
            datetime=datetime.utcnow(),
        )
        if total < file_size:
            # File too small
            raise EOFError("The downloaded file was smaller than expected!")

        if total > file_size:
            raise EOFError("The downloaded file was larger than expected!")
