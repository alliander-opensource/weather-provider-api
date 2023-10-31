#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import glob
from datetime import datetime
from typing import List

from dateutil.relativedelta import relativedelta
from loguru import logger

from weather_provider_api.routers.weather.repository.repository import WeatherRepositoryBase
from weather_provider_api.routers.weather.sources.cds.client.utils_era5 import era5_update
from weather_provider_api.routers.weather.sources.cds.factors import era5sl_factors
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.grid_helpers import round_coordinates_to_wgs84_grid


class ERA5SLRepository(WeatherRepositoryBase):
    """
    A class that holds all functionality (excepting the downloader) for the ERA5 Single Levels Repository
    """

    def __init__(self):
        super().__init__()
        self.repository_name = "CSD ERA5 Single Levels"
        logger.debug(f"Initializing {self.repository_name} repository")
        self.file_prefix = "ERA5SL"
        self.runtime_limit = 3 * 60  # 3 hours maximum runtime
        self.permanent_suffixes = ["INCOMPLETE", "TEMP"]
        self.grid_resolution = 0.25
        self.file_identifier_length = 7
        self.age_of_permanence_in_months = 3

        logger.debug(f"Initialized {self.repository_name} repository")

    @staticmethod
    def _get_repo_sub_folder():
        return "ERA5_SL"

    @property
    def first_day_of_repo(self):
        first_day_of_repo = datetime.utcnow() - relativedelta(years=12, days=5)
        first_day_of_repo = first_day_of_repo.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return first_day_of_repo

    @property
    def last_day_of_repo(self):
        last_day_of_repo = datetime.utcnow() - relativedelta(days=5)
        last_day_of_repo = last_day_of_repo.replace(hour=0, minute=0, second=0, microsecond=0)
        return last_day_of_repo

    def update(self):
        """
            The implementation of the WeatherRepository required update() function.
            This function handles all the required actions to update the repository completely, but taking into
            account its set runtime_limit. If based on the time of completion of other downloaded files this session
            the next file wouldn't complete within the runtime_limit, the update process halts.
            (if no other downloads were made yet, a generous rough estimate is used)
        Returns:
            A RepositoryUpdateResult value indicating a completion, time-out or failure of the update process
        """

        # Always start with a nicely cleaned repository
        self.cleanup()

        logger.info(f"ERA5 Single Levels Update - Storage in: {self.repository_folder} ")
        return era5_update(
            self.file_prefix,
            self.repository_folder,
            (self.first_day_of_repo, self.last_day_of_repo),
            "reanalysis-era5-single-levels",
            "reanalysis",
            [era5sl_factors[x] for x in list(era5sl_factors.keys())],
            (self.grid_resolution, self.grid_resolution),
            era5sl_factors,
            self.runtime_limit,
            True,
        )

    def _delete_files_outside_of_scope(self):
        """
            A function that deletes all files in the repository with a date not inside the repository's scope.
            All files labeled as either before or after the given scope will be deleted.
        Returns:
            Nothing. Successful means the all files outside the scope were deleted.
        """
        len_filename_until_date = len(str(self.repository_folder.joinpath(self.file_prefix))) + 1

        for file_name in glob.glob(str(self.repository_folder.joinpath(self.file_prefix)) + "*.nc"):
            file_year = int(file_name[len_filename_until_date : len_filename_until_date + 4])
            file_month = int(file_name[len_filename_until_date + 5 : len_filename_until_date + 7])

            if (
                file_year < self.first_day_of_repo.year
                or file_year > self.last_day_of_repo.year
                or (file_year == self.first_day_of_repo.year and file_month < self.first_day_of_repo.month)
                or (file_year == self.last_day_of_repo.year and file_month > self.last_day_of_repo.month)
            ):
                logger.debug(
                    f"Deleting file [{file_name}] because it does not lie in the "
                    f"repository scope ({self.first_day_of_repo, self.last_day_of_repo})"
                )
                self._safely_delete_file(file_name)

    def _get_file_list_for_period(self, start: datetime, end: datetime):
        """
            A function that retrieves a list of files in the repository associated with the requested period of time
        Args:
            start:  A datetime containing the start of the requested period of time.
            end:    A datetime containing the end of the requested period of time.
        Returns:
            A list of files (in string format) that indicate the files containing data for the requested period.
        """
        self.cleanup()

        len_filename_until_date = len(str(self.repository_folder.joinpath(self.file_prefix))) + 1
        logger.info(
            f"Searching for ERA5 Single Levels files in repository folder: "
            f"{self.repository_folder.joinpath(self.file_prefix)}"
        )
        full_list_of_files = glob.glob(str(self.repository_folder.joinpath(self.file_prefix)) + "*.nc")
        list_of_filtered_files = []
        for file in full_list_of_files:
            file_year = int(file[len_filename_until_date : len_filename_until_date + 4])
            file_month = int(file[len_filename_until_date + 5 : len_filename_until_date + 7])
            date_for_filename = datetime(year=file_year, month=file_month, day=15)

            if start.replace(day=1) < date_for_filename < datetime(year=end.year, month=end.month, day=28):
                # If the file is within the requested period, save it to the list of filtered files
                list_of_filtered_files.append(file)

        return list_of_filtered_files

    def get_grid_coordinates(self, coordinates: List[GeoPosition]) -> List[GeoPosition]:
        # Rounds a list of GeoPositions to the resolution set through grid_resolution
        return round_coordinates_to_wgs84_grid(
            coordinates=coordinates,
            grid_resolution_lat_lon=(self.grid_resolution, self.grid_resolution),
            starting_points_lat_lon=(50.75, 3.2),  # Used to properly round values
        )
