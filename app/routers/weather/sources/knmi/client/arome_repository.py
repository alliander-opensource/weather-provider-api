#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

import glob
import re
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List

import netCDF4 as nc
import pandas as pd
import pygrib
import pytz
import xarray as xr
from dateutil.relativedelta import relativedelta

from app.routers.weather.repository.repository import (
    WeatherRepositoryBase,
    RepositoryUpdateResult,
)
from app.routers.weather.sources.knmi.client.knmi_downloader import KNMIDownloader
from app.routers.weather.sources.knmi.knmi_factors import arome_factors
from app.routers.weather.utils.geo_position import GeoPosition
from app.routers.weather.utils.grid_helpers import round_to_grid


class AromeRepository(WeatherRepositoryBase):
    """
    A class that holds all functionality (excepting the downloader) for the KNMI Harmonie Arome Repository
    """

    def __init__(self):
        super().__init__()
        self.repository_name = "KNMI Harmonie (Arome)"
        self.file_prefix = "AROME"
        self.runtime_limit = 60 * 60 * 3  # 3 hours maximum runtime
        self.permanent_suffixes = ["0000", "0600", "1200", "1800"]
        self.dataset_name = "harmonie_arome_cy40_p1"
        self.dataset_version = "0.2"
        self.file_identifier_length = 13

        self.first_day_of_repo = datetime.utcnow() - relativedelta(years=1)
        self.first_day_of_repo = self.first_day_of_repo.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        self.last_day_of_repo = (
            datetime.utcnow()
        )  # Update will translate this to the proper 6 hour block
        self.last_day_of_repo = self.last_day_of_repo.replace(
            minute=0, second=0, microsecond=0
        )

        self.logger.debug(
            f"Initialized {self.repository_name} repository", datetime=datetime.utcnow()
        )

    def _get_repo_sub_folder(self):
        return "AROME"

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
        self.cleanup()  # Always start with a cleaned up repository
        update_start = datetime.utcnow()
        items_processed = 0
        average_per_item = (
            300  # Assuming 5 minutes processing time for the first item to be safe
        )
        update_forced_end = update_start + relativedelta(seconds=self.runtime_limit)

        self.logger.info(
            f"Updating {self.repository_name} with a forced end time of [{update_forced_end}]",
            datetime=datetime.utcnow(),
        )

        prediction_to_check = self._nearest_prediction_to_datetime(
            self.last_day_of_repo
        )

        while prediction_to_check >= self.first_day_of_repo:
            if items_processed != 0:
                average_per_item = (
                    datetime.utcnow() - update_start
                ).total_seconds() / items_processed
            if (
                average_per_item
                > (update_forced_end - datetime.utcnow()).total_seconds()
            ):
                self.logger.info(
                    "No time remaining to process the next file. Aborting update process",
                    datetime=datetime.utcnow(),
                )
                return RepositoryUpdateResult.timed_out

            if self._prediction_unavailable(prediction_to_check):
                self.logger.debug(
                    f"Gathering prediction of {prediction_to_check}",
                    datetime=datetime.utcnow(),
                )

                file_to_download = (
                    "harm40_v1_p1_"
                    + str(prediction_to_check.year)
                    + str(prediction_to_check.month).zfill(2)
                    + str(prediction_to_check.day).zfill(2)
                    + str(prediction_to_check.hour).zfill(2)
                )

                downloader = KNMIDownloader(
                    self.dataset_name, self.dataset_version, file_to_download, 1
                )
                self._empty_folder(
                    Path(tempfile.gettempdir()).joinpath(downloader.dataset_name)
                )
                download_folder, files_saved = downloader.knmi_download_request()

                self._process_prediction_files(
                    download_folder, files_saved, prediction_to_check
                )
                items_processed += 1
            else:
                self.logger.debug(
                    f"Prediction {prediction_to_check} already in repository"
                )

            prediction_to_check -= relativedelta(hours=6)
        return RepositoryUpdateResult.completed

    def _prediction_unavailable(self, datetime_to_check: datetime):
        # Function to check if a prediction file already exists. True means "no file available"
        if self.repository_folder.joinpath(
            self.file_prefix
            + "_"
            + str(datetime_to_check.year)
            + str(datetime_to_check.month).zfill(2)
            + str(datetime_to_check.day).zfill(2)
            + "_"
            + str(datetime_to_check.hour).zfill(2)
            + "00.nc"
        ).exists():
            return False
        return True

    def _process_prediction_files(
        self, download_folder, files_downloaded, prediction_datetime: datetime
    ):
        # A function that operates as a production line, handling the full conversion from a packed downloaded file, to
        # many grib files, to several formatted NetCDF4 files. Afterwards folders are cleaned up as well.
        for file in files_downloaded:
            if self._unpack_downloaded_file(download_folder, file):
                self._convert_unpacked_to_netcdf4(download_folder)
                self._combine_hourly_files(download_folder, prediction_datetime)
                self._empty_folder(download_folder)

    @staticmethod
    def _nearest_prediction_to_datetime(datetime_to_check: datetime) -> datetime:
        """
            A function that calculates the nearest prediction moment (CET) based on the current time (UTC).
            (The release moments are based on CET time)
        Args:
            datetime_to_check:  A datetime containing the moment to verify the nearest release for.
        Returns:
            A datetime holding the nearest prediction moment to the requested datetime.
        """
        lag_knmi = 5  # There is a known 5 hour calculation lag to take into account

        # Determine current CET Time
        t_cet = datetime_to_check.astimezone(pytz.timezone("Europe/Amsterdam"))
        t_cet += (
            t_cet.utcoffset()
        )  # Add the offset to get the actual time in the values
        # TODO: This should be easier and less messy

        # Subtract the lag
        t_cet = t_cet.replace(tzinfo=None, microsecond=0) - relativedelta(
            hours=lag_knmi
        )

        # Round the result down to the nearest preceding block of 6 hours.
        new_hour = (t_cet.hour // 6) * 6
        t_cet = t_cet.replace(hour=new_hour, minute=0, second=0)

        return t_cet

    def _unpack_downloaded_file(self, download_folder, file_name):
        # Function that unpacks the tar-files that the predictions are downloaded as.
        self.logger.debug("Unpacking file: " + file_name.get("filename"))
        try:
            tar = tarfile.open(
                Path(download_folder).joinpath(file_name.get("filename"))
            )
            tar.extractall(path=Path(download_folder))
            tar.close()
            return True
        except Exception as e:
            self.logger.error(
                f"Could not unpack tarfile [{file_name}]", datetime=datetime.utcnow()
            )
            raise e

    def _convert_unpacked_to_netcdf4(self, download_folder):
        # A function that handles the many small GRIB files that were unpacked and formats those into NetCDF4
        grib_files = glob.glob(str(Path(download_folder).joinpath("HA40_N25_*_GB")))

        for file in grib_files:
            pyg_file = pygrib.open(str(file))
            file_time, prediction_hour = self._get_time_from_file(file)

            ds = None

            for pyg_line in pyg_file:
                # Conversion of grib lines into an usable dataset
                ds_temp = self._grib_line_to_ds(pyg_line, file_time, prediction_hour)

                if ds_temp is not None:
                    if ds is None:
                        ds = ds_temp
                    else:
                        ds = xr.merge([ds, ds_temp])

            save_file = Path(download_folder).joinpath(
                self.file_prefix
                + str(file_time.year)
                + str(file_time.month).zfill(2)
                + str(file_time.day).zfill(2)
                + "_"
                + str(file_time.hour).zfill(2)
                + "00_PREDICTION_"
                + str(prediction_hour).zfill(2)
                + "00.nc"
            )

            ds = ds.unstack("coord")
            ds.to_netcdf(path=save_file, format="NETCDF4")

    @staticmethod
    def _get_time_from_file(file) -> (datetime, datetime):
        # Function that parses the time-span a file represents into the datetime the prediction was made
        # and the hour it predicts.
        year = int(file[-21:-17])
        month = int(file[-17:-15])
        day = int(file[-15:-13])
        hour = int(file[-13:-11])
        file_time = datetime(year=year, month=month, day=day, hour=hour)

        # hourly prediction datetime
        predictive_hour = int(file[-7:-5])

        return file_time, predictive_hour

    def _grib_line_to_ds(self, grib_line, file_time, prediction_hour):
        """
            A function that parses the Harmonie Arome GRIB lines into an Xarray Dataset.
        Args:
            grib_line:          A line from a GRIB file (in string format).
            file_time:          The datetime indicating  the prediction moment.
            prediction_hour:    The predictive hour for which the line is intended.
        Returns:
            An Xarray Dataset containing the properly formatted weather data that was interpreted from the GRIB line.
        """
        grib_param = grib_line["parameterName"]
        grib_level_type = "_".join(
            re.findall("[A-Z][^A-Z]*", grib_line["typeOfLevel"])
        ).lower()
        grib_level = grib_line["level"]

        # The 0000 hour-file of every prediction also includes accumulated totals for the entire prediction.
        # These are stored on a rotated grids for some reason. As we don't need them, no sense in processing these..
        if float(grib_line["latitudeOfFirstGridPointInDegrees"]) < 40:
            return None

        # Sometimes codes not explained for the dataset are also included (codes 17, 20 and 18 at the moment of writing)
        # These we leave out. The same goes for 'T Temperature K' which appears to be a copy of code 11 at 0m level.
        if grib_param not in arome_factors or grib_param in ("T Temperature K", "1"):
            return None

        lats, lons = self._build_grid_block(grib_line)

        written_name = f"{arome_factors[grib_param]}"
        if arome_factors[grib_param][0] == "_":
            written_name = f'{grib_line["stepType"]}{written_name}'

        if grib_level == 0 and grib_level_type == "above_ground":
            written_name = f"surface_{written_name}"
        else:
            written_name = f"{grib_level}m_{grib_level_type}_{written_name}"

        # Reshape the data to match the dimensions for the dataset
        grib_values = grib_line["values"].reshape(len(lats) * len(lons))

        # Now to setup an Xarray Dataset to hold all of our information
        data_dict = {written_name: (["time", "coord"], [grib_values])}
        prediction_time = file_time + relativedelta(hours=prediction_hour)

        ds = xr.Dataset(
            data_vars=data_dict,
            coords={
                "prediction_moment": [file_time],
                "time": [prediction_time],
                "coord": pd.MultiIndex.from_product([lats, lons], names=["lat", "lon"]),
            },
        )
        ds.time.encoding["units"] = "hours since 2018-01-01"
        return ds

    @staticmethod
    def _build_grid_block(pyg_line):
        # A function to build a list for both latitudes and longitudes used in a prediction file. Makes up a grid.
        lat_first = float(pyg_line["latitudeOfFirstGridPointInDegrees"])
        lat_last = float(pyg_line["latitudeOfLastGridPointInDegrees"])

        lon_first = float(pyg_line["longitudeOfFirstGridPointInDegrees"])
        lon_last = float(pyg_line["longitudeOfLastGridPointInDegrees"])

        lat_step = float(pyg_line["jDirectionIncrement"])
        lon_step = float(pyg_line["iDirectionIncrement"])

        latitudes = list(
            range(
                int(lat_first * 1000),
                int(lat_last * 1000) + int(lat_step),
                int(lat_step),
            )
        )
        longitudes = list(
            range(
                int(lon_first * 1000),
                int(lon_last * 1000) + int(lon_step),
                int(lon_step),
            )
        )

        latitudes = [x / 1000 for x in latitudes]
        longitudes = [x / 1000 for x in longitudes]

        return latitudes, longitudes

    def _combine_hourly_files(self, download_folder, prediction_time):
        # A function that combines the files for prediction hour with a prediction into files for that prediction
        self.logger.info(
            f"Fusing hourly files for [{prediction_time} into [{self.repository_folder}]",
            datetime=datetime.utcnow(),
        )
        prediction_files = sorted(
            glob.glob(str(Path(download_folder).joinpath("AROME*.nc")))
        )

        # TODO: Verify that the only .nc files are those that need to be fused
        ds = None

        for prediction_file in prediction_files:
            with xr.open_dataset(prediction_file) as ds_query:
                ds_query.load()
                if ds is None:
                    ds = ds_query
                else:
                    ds = xr.merge([ds, ds_query])

        save_file_name = (
            str(Path(self.repository_folder).joinpath(self.file_prefix))
            + "_"
            + str(prediction_time.year)
            + str(prediction_time.month).zfill(2)
            + str(prediction_time.day).zfill(2)
            + "_"
            + str(prediction_time.hour).zfill(2)
            + "00.nc"
        )

        self.logger.debug(
            f"Saving [{prediction_time} to  [{save_file_name}]",
            datetime=datetime.utcnow(),
        )

        # TODO: The current process of first saving everything into an uncompressed file is extremely dirty
        #       This has to be fixed.

        # Save uncompressed file
        ds.to_netcdf(save_file_name + "UC", format="NETCDF4", engine="netcdf4")

        # Set up compressed file
        source_file = nc.Dataset(save_file_name + "UC")
        compressed_netcdf4_file = nc.Dataset(save_file_name, mode="w")

        # Create the dimensions of the file
        for name, dim in source_file.dimensions.items():
            compressed_netcdf4_file.createDimension(
                name, len(dim) if not dim.isunlimited() else None
            )

        # Copy the global attributes
        compressed_netcdf4_file.setncatts(
            {a: source_file.getncattr(a) for a in source_file.ncattrs()}
        )

        # Create the variables in the file
        for name, var in source_file.variables.items():
            compressed_netcdf4_file.createVariable(
                name, var.dtype, var.dimensions, zlib=True
            )

            # Copy the variable attributes
            compressed_netcdf4_file.variables[name].setncatts(
                {a: var.getncattr(a) for a in var.ncattrs()}
            )

            # Copy the variables values (as 'f4' eventually)
            compressed_netcdf4_file.variables[name][:] = source_file.variables[name][:]

        # Save the file
        source_file.close()
        compressed_netcdf4_file.close()

        # Remove the uncompressed file
        self._safely_delete_file(save_file_name + "UC")

    def _empty_folder(self, download_folder):
        # Function that cleans up the temporary download folder
        self.logger.debug(
            f"Emptying up the folder [{download_folder}]", datetime=datetime.utcnow()
        )
        for file in glob.glob(str(Path(download_folder)) + "*.*"):
            try:
                Path(file).unlink()
            except Exception as e:
                self.logger.error(f"Could not delete [{file}]: {e}")
                raise e

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
            file_date = datetime(
                year=int(
                    file_name[len_filename_until_date : len_filename_until_date + 4]
                ),
                month=int(
                    file_name[len_filename_until_date + 4 : len_filename_until_date + 6]
                ),
                day=int(
                    file_name[len_filename_until_date + 6 : len_filename_until_date + 8]
                ),
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            if file_date < self.first_day_of_repo or file_date > self.last_day_of_repo:
                self.logger.debug(
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
        self.logger.debug(f"Checking files in [{self.repository_folder}]")
        print(start, end)
        len_filename_until_date = (
            len(str(self.repository_folder.joinpath(self.file_prefix))) + 1
        )

        full_list_of_files = glob.glob(
            str(self.repository_folder.joinpath(self.file_prefix)) + "*.nc"
        )
        list_of_filtered_files = []

        for file in full_list_of_files:
            file_date = datetime(
                year=int(file[len_filename_until_date : len_filename_until_date + 4]),
                month=int(
                    file[len_filename_until_date + 4 : len_filename_until_date + 6]
                ),
                day=int(
                    file[len_filename_until_date + 6 : len_filename_until_date + 8]
                ),
                hour=int(
                    file[len_filename_until_date + 9 : len_filename_until_date + 11]
                ),
                minute=0,
                second=0,
                microsecond=0,
            )

            if start < file_date < end:
                # If the file is within the requested period, save it to the list of filtered files
                list_of_filtered_files.append(file)

        return list_of_filtered_files

    def get_grid_coordinates(self, coordinates: List[GeoPosition]) -> List[GeoPosition]:
        """ Rounds a list of GeoPositions to the resolution set through grid_resolution """
        return round_to_grid(coordinates, 0.023, 0.037, 49, 0)
