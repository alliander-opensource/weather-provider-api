#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.

import glob
import math
from datetime import datetime
from pathlib import Path
from typing import List

from dateutil.relativedelta import relativedelta

from app.routers.weather.repository.repository import (
    WeatherRepositoryBase,
    RepositoryUpdateResult,
)
from app.routers.weather.sources.cds.client import downloader
from app.routers.weather.sources.cds.factors import era5sl_factors
from app.routers.weather.utils.geo_position import GeoPosition
from app.routers.weather.utils.grid_helpers import round_to_grid


def _repository_callback(*args, **kwargs):
    print("Callback - Received args:", args)
    print("Callback - Received kwargs:", kwargs)


class ERA5SLRepository(WeatherRepositoryBase):
    """
    A class that holds all functionality (excepting the downloader) for the ERA5 Single Levels Repository
    """

    def __init__(self):
        super().__init__()
        self.repository_name = "CSD ERA5 Single Levels"
        self.logger.debug(
            f"Initializing {self.repository_name} repository",
            datetime=datetime.utcnow(),
        )
        self.file_prefix = "ERA5SL"
        self.runtime_limit = 60 * 60 * 3  # 3 hours maximum runtime
        self.permanent_suffixes = ["INCOMPLETE", "TEMP"]
        self.grid_resolution = 0.25
        self.file_identifier_length = 7
        self.age_of_permanence_in_months = 3

        self.logger.debug(
            f"Initialized {self.repository_name} repository", datetime=datetime.utcnow()
        )

    def _get_repo_sub_folder(self):
        return "ERA5_SL"

    @staticmethod
    def get_first_day_of_repo():
        first_day_of_repo = datetime.utcnow() - relativedelta(years=3, days=5)
        first_day_of_repo = first_day_of_repo.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return first_day_of_repo

    @staticmethod
    def get_last_day_of_repo():
        last_day_of_repo = datetime.utcnow() - relativedelta(days=5)
        last_day_of_repo = last_day_of_repo.replace(hour=0, minute=0, second=0, microsecond=0)
        return last_day_of_repo

    def update(self):
        """
            The implementation of the WeatherRepository required update() function.
            This function handles all of the required actions to update the repository completely, but taking into
            account its set runtime_limit. If based on the time of completion of other downloaded files this session
            the next file wouldn't complete within the runtime_limit, the update process halts.
            (if no other downloads were made yet, a generous rough estimate is used)
        Returns:
            A RepositoryUpdateResult value indicating a completion, time-out or failure of the update process
        """
        # Always start with a nicely cleaned repository
        self.cleanup()

        update_start = datetime.utcnow()
        items_processed = 0
        average_time_per_item = (
            1200  # Assuming 20 minutes of processing time for the first item to be safe
        )
        update_forced_end = update_start + relativedelta(seconds=self.runtime_limit)

        self.logger.info(
            f"Updating {self.repository_name} with a forced end time of [{update_forced_end}]",
            datetime=datetime.utcnow(),
        )

        active_month_for_update = self.get_last_day_of_repo().replace(
            day=1
        )  # Starting at the most recent month. The first day is used to ensure proper pickup of even the oldest month
        while active_month_for_update >= self.get_first_day_of_repo():
            if items_processed != 0:
                average_time_per_item = (
                    datetime.utcnow() - update_start
                ).total_seconds() / items_processed
            if (
                average_time_per_item
                > (update_forced_end - datetime.utcnow()).total_seconds()
            ):
                self.logger.info(
                    f"No time remaining to process the next file. Aborting update process",
                    datetime=datetime.utcnow(),
                )
                return RepositoryUpdateResult.timed_out

            file_prefix = (
                str(self.repository_folder.joinpath(self.file_prefix))
                + "_"
                + str(active_month_for_update.year)
                + "_"
                + str(active_month_for_update.month).zfill(2)
            )

            if self._file_requires_update(file_prefix):
                self.logger.debug(
                    f"Updating for ({active_month_for_update.year}, {active_month_for_update.month})"
                )

                self._download_era5sl_file(
                    [era5sl_factors[x] for x in list(era5sl_factors.keys())],
                    list([active_month_for_update.year]),
                    list([active_month_for_update.month]),
                    list(range(1, 32)),
                    [51, 3.5, 53.75, 7.25],
                    str(file_prefix) + "_UNFORMATTED.nc",
                )

                self._format_downloaded_file(str(file_prefix) + "_UNFORMATTED.nc")

                Path(file_prefix + "_UNFORMATTED.nc").rename(
                    file_prefix + "_FORMATTED.nc"
                )

                self._finalize_formatted_file(file_prefix)
                items_processed += 1

            active_month_for_update -= relativedelta(months=1)
        return RepositoryUpdateResult.completed

    def _file_requires_update(self, file_prefix: str):
        """
            A Function that checks if a file with a given prefix exists, and if it is a repository file that should
             be updated.
        Args:
            file_prefix:    The prefix of the filename to check. A file extension of .nc is assumed.
        Returns:
            Returns True if the file should be updated, and False if no update is required.

        """
        if not glob.glob(file_prefix + "*.nc"):  # Globbing for all suffix
            return True  # No file exists yet, so must update!

        if Path(file_prefix + "_INCOMPLETE.nc").exists():
            return True  # File is or was the active month and is probably not completed yet. Must update

        if Path(file_prefix + "_TEMP.nc").exists():
            # If the file has the _TEMP suffix it only needs an update when it should've had a definitive update
            file_date = datetime(
                year=int(file_prefix[-7:-3]), month=int(file_prefix[-2:]), day=1
            )
            current_date_of_permanence = (
                self.get_last_day_of_repo()
                - relativedelta(months=self.age_of_permanence_in_months)
            ).replace(day=1)

            # If the file is older than the three months required before permanence, it can be replaced by its permanent
            # version.
            if file_date < current_date_of_permanence:
                return True

        if Path(file_prefix + "_UNFORMATTED.nc").exists():
            # If somehow only an unformatted file exists, an update is definitely required
            return True

        return False

    def _format_downloaded_file(self, unformatted_file: str):
        """
            A function that formats an unformatted file
        Args:
            unformatted_file:   A string containing the full location of the unformatted file.
        Returns:
            Nothing. Completion is assumed to have generated
        """
        self.logger.debug(f"Formatting downloaded file [{unformatted_file}]")
        ds_temp = self.load_file(Path(unformatted_file))

        # Delete attributes
        ds_temp.attrs = {}

        # Check for the rare occurrence in which both temporary and permanent data exist in a download.
        if "expver" in ds_temp.keys():
            self.logger.debug(
                f"The loaded dataset contains both data for the regular ERA5SL as well as the Temporary version"
            )

            expver_1, expver_5 = False, False
            ds_expver_test = ds_temp.where(ds_temp.expver == 1)
            if not math.isnan(ds_expver_test.d2m.values[0][0][0][0]):
                self.logger.debug(f"Values for EXPVER=1 (Permanent) weather were found")
                expver_1 = True

            ds_expver_test = ds_temp.where(ds_temp.expver == 5)
            if not math.isnan(ds_expver_test.d2m.values[0][0][0][0]):
                self.logger.debug(f"Values for EXPVER=5 (Temporary) weather were found")
                expver_5 = True

            if expver_5 and expver_1:
                self.logger.error(
                    f"Both Temporary and Permanent weather data were found. Aborting placement in repository"
                )
                raise ValueError(
                    f"Both Temporary and Permanent weather data exist within the file [{unformatted_file}]."
                )

            if not expver_5 and not expver_1:
                self.logger.error(
                    f"Neither Temporary or Permanent weather data were found. Aborting placement in repository"
                )
                raise ValueError(
                    f"Neither Temporary or Permanent weather data exist within the file [{unformatted_file}]."
                )

            # Select the proper sub-selection
            if expver_5:
                ds_temp = ds_temp.where(ds_temp.expver == 5, drop=True)
            else:
                ds_temp = ds_temp.where(ds_temp.expver == 1, drop=True)

            # Remove the expver dimension completely now that we only have a single type remaining.
            ds_temp = ds_temp.reset_index(['longitude', 'latitude', 'time']).drop('expver').squeeze()

        # Rename factors to their longer names
        for factor in ds_temp.variables.keys():
            if factor in era5sl_factors:
                ds_temp = ds_temp.rename_vars({factor: era5sl_factors[factor]})

        ds_temp.time.encoding["units"] = "hours since 2016-01-01"
        ds_temp = ds_temp.rename(name_dict={"latitude": "lat", "longitude": "lon"})
        ds_temp.to_netcdf(path=unformatted_file, format="NETCDF4", engine="netcdf4")

    def _finalize_formatted_file(self, file_prefix: str):
        """
            A function that finalizes a formatted file by renaming it into the proper suffix (or lack thereof) for its
            type.
            No Suffix:      Permanent File
            _INCOMPLETE:    As of yet incomplete file for the currently being processed month.
            _TEMP:          Complete file using not yet verified values. Data is confirmed or replaced in about three
                            months by the permanent data.
        Args:
            file_prefix:    The prefix for the file to verify. Does not included the assumed "_FORMATTED.nc" suffix and
                            file extension.
        Returns:
            Doesn't return anything, but renames the _FORMATTED.nc file as appropriate for the data in it, based on
            data age.
        """
        # First we verify that the required formatted file exists
        if not Path(file_prefix + "_FORMATTED.nc").exists():
            self.logger.error(
                f"A formatted file for [{file_prefix}] was not found",
                datetime=datetime.utcnow(),
            )
            raise FileNotFoundError(
                f"A formatted file for [{file_prefix}] was not found"
            )

        if Path(file_prefix + "_TEMP.nc").exists():
            self._safely_delete_file(file_prefix + "_TEMP.nc")
        if Path(file_prefix + "_INCOMPLETE.nc").exists():
            self._safely_delete_file(file_prefix + "_INCOMPLETE.nc")

        file_date = datetime(
            year=int(file_prefix[-7:-3]), month=int(file_prefix[-2:]), day=1
        )
        current_incomplete_month = self.get_last_day_of_repo().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        oldest_temporary_month = current_incomplete_month - relativedelta(months=3)

        if current_incomplete_month == file_date:
            # If currently processing the incomplete month, rename it as such
            Path(file_prefix + "_FORMATTED.nc").rename(file_prefix + "_INCOMPLETE.nc")
        elif oldest_temporary_month < file_date < current_incomplete_month:
            # If currently processing a temporary file that is not incomplete, rename it as such
            Path(file_prefix + "_FORMATTED.nc").rename(file_prefix + "_TEMP.nc")
        else:
            # If currently processing a permanent file, rename it as such
            Path(file_prefix + "_FORMATTED.nc").rename(file_prefix + ".nc")

    def _download_era5sl_file(
        self, weather_factors, years, months, days, area_box, target_location
    ):
        """
            A function that download a NetCDF file to the target location, containing the requested factors for an
            also requested range of years, months, days and locations.
        Args:
            weather_factors:    A list of factors to be downloaded (in string format)
            years:              A list of years to be requested (numeric)
            months:             A list of months to be requested (numeric)
            days:               A list of days to be requested (numeric)
            area_box:           A boxed grid of coordinates (x1, y1 to x2, y2) for which all locations will be requested
            target_location:    The file location to which the result should be saved after downloading.
        Returns:
            Returns nothing, but success means a result file will exist at the given target location.
        """
        c = downloader.Client(
            persist_request_callback=_repository_callback(), debug=True, verify=True
        )
        c.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": weather_factors,
                "year": years,
                "month": months,
                "day": days,
                "time": [
                    "00:00",
                    "01:00",
                    "02:00",
                    "03:00",
                    "04:00",
                    "05:00",
                    "06:00",
                    "07:00",
                    "08:00",
                    "09:00",
                    "10:00",
                    "11:00",
                    "12:00",
                    "13:00",
                    "14:00",
                    "15:00",
                    "16:00",
                    "17:00",
                    "18:00",
                    "19:00",
                    "20:00",
                    "21:00",
                    "22:00",
                    "23:00",
                ],
                "area": area_box,
                "grid": [self.grid_resolution, self.grid_resolution],
                "format": "netcdf",
            },
            target_location,
        )

    def _delete_files_outside_of_scope(self):
        """
            A function that deletes all files in the repository with a date not inside the repository's scope.
            All files labeled as either before or after the given scope will be deleted.
        Returns:
            Nothing. Successful means the all files outside of the scope were deleted.
        """
        len_filename_until_date = (
            len(str(self.repository_folder.joinpath(self.file_prefix))) + 1
        )

        for file_name in glob.glob(
            str(self.repository_folder.joinpath(self.file_prefix)) + "*.nc"
        ):
            file_year = int(
                file_name[len_filename_until_date : len_filename_until_date + 4]
            )
            file_month = int(
                file_name[len_filename_until_date + 5 : len_filename_until_date + 7]
            )

            if (
                file_year < self.get_first_day_of_repo().year
                or file_year > self.get_last_day_of_repo().year
                or (
                    file_year == self.get_first_day_of_repo().year
                    and file_month < self.get_first_day_of_repo().month
                )
                or (
                    file_year == self.get_last_day_of_repo().year
                    and file_month > self.get_last_day_of_repo().month
                )
            ):
                self.logger.debug(
                    f"Deleting file [{file_name}] because it does not lie in the "
                    f"repository scope ({self.get_first_day_of_repo(), self.get_last_day_of_repo()})"
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

        len_filename_until_date = (
            len(str(self.repository_folder.joinpath(self.file_prefix))) + 1
        )
        full_list_of_files = glob.glob(
            str(self.repository_folder.joinpath(self.file_prefix)) + "*.nc"
        )
        list_of_filtered_files = []
        for file in full_list_of_files:
            file_year = int(file[len_filename_until_date : len_filename_until_date + 4])
            file_month = int(
                file[len_filename_until_date + 5 : len_filename_until_date + 7]
            )
            date_for_filename = datetime(year=file_year, month=file_month, day=15)

            if (
                start.replace(day=1)
                < date_for_filename
                < datetime(year=end.year, month=end.month, day=28)
            ):
                # If the file is within the requested period, save it to the list of filtered files
                list_of_filtered_files.append(file)

        return list_of_filtered_files

    def get_grid_coordinates(self, coordinates: List[GeoPosition]) -> List[GeoPosition]:
        # Rounds a list of GeoPositions to the resolution set through grid_resolution
        return round_to_grid(coordinates, self.grid_resolution, self.grid_resolution)