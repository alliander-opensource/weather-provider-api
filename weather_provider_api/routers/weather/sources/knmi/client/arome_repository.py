#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import glob
import re
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import netCDF4 as nc
import numpy as np
import pandas as pd
import pytz
import xarray as xr
from dateutil.relativedelta import relativedelta

from weather_provider_api.routers.weather.repository.repository import WeatherRepositoryBase, RepositoryUpdateResult
from weather_provider_api.routers.weather.sources.knmi.client.knmi_downloader import KNMIDownloader
from weather_provider_api.routers.weather.sources.knmi.knmi_factors import arome_factors
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.grid_helpers import round_coordinates_to_wgs84_grid


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

        self.time_encoding = "hours since 2018-01-01"  # Used to keep values usable for at least the upcoming decennium

        self.logger.debug(f"Initialized {self.repository_name} repository", datetime=datetime.utcnow())
        try:
            import cfgrib
        except RuntimeError as e:
            self.logger.error(f"A problem occurred with the ECCODES library: {e}")
            self.logger.warning("This means that though interactions with the existing repository will still work, "
                                "the repository cannot be updated!")

    @staticmethod
    def _get_repo_sub_folder():
        return "AROME"

    @staticmethod
    def get_first_day_of_repo():
        first_day_of_repo = datetime.utcnow() - relativedelta(years=1)
        first_day_of_repo = first_day_of_repo.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return first_day_of_repo

    @staticmethod
    def get_last_day_of_repo():
        last_day_of_repo = datetime.utcnow()  # Update will translate this to the proper 6 hour block
        last_day_of_repo = last_day_of_repo.replace(minute=0, second=0, microsecond=0)
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
        if 'cfgrib' not in sys.modules:
            self.logger.error("CANNOT PERFORM UPDATE: 'cfgrib' installation is not operational.")
            quit()

        # Always start with a cleaned up repository
        self.cleanup()

        update_start = datetime.utcnow()
        items_processed = 0
        average_per_item = 300  # Assuming 5 minutes processing time for the first item to be safe
        update_forced_end = update_start + relativedelta(seconds=self.runtime_limit)

        self.logger.info(
            f"Updating {self.repository_name} with a forced end time of [{update_forced_end}]",
            datetime=datetime.utcnow()
        )

        prediction_to_check = self._nearest_prediction_to_datetime(self.get_last_day_of_repo())

        while prediction_to_check >= self.get_first_day_of_repo():
            if items_processed != 0:
                average_per_item = (datetime.utcnow() - update_start).total_seconds() / items_processed
            if average_per_item > (update_forced_end - datetime.utcnow()).total_seconds():
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

                downloader = KNMIDownloader(self.dataset_name, self.dataset_version, file_to_download, 1)
                self._empty_folder(Path(tempfile.gettempdir()).joinpath(downloader.dataset_name))
                download_folder, files_saved = downloader.knmi_download_request()

                self._process_prediction_files(download_folder, files_saved, prediction_to_check)
                items_processed += 1
            else:
                self.logger.debug(f"Prediction {prediction_to_check} already in repository")

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
            self, download_folder: str, files_downloaded: List[Dict], prediction_datetime: datetime
    ):
        # A function that operates as a production line, handling the full conversion from a packed downloaded file, to
        # many grib files, to several formatted NetCDF4 files. Afterwards folders are cleaned up as well.
        for file in files_downloaded:
            filename = file.get("filename")
            if self._unpack_downloaded_file(download_folder, filename):
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
        t_cet += t_cet.utcoffset()  # Add the offset to get the actual time in the values

        # Subtract the lag
        t_cet = t_cet.replace(tzinfo=None, microsecond=0) - relativedelta(hours=lag_knmi)

        # Round the result down to the nearest preceding block of 6 hours.
        new_hour = (t_cet.hour // 6) * 6
        t_cet = t_cet.replace(hour=new_hour, minute=0, second=0)

        return t_cet

    def _unpack_downloaded_file(self, download_folder: str, file_name: str):
        # Function that unpacks the tar-files that the predictions are downloaded as.
        self.logger.debug("Unpacking file: " + file_name)
        try:
            tar = tarfile.open(Path(download_folder).joinpath(file_name))
            tar.extractall(path=Path(download_folder))
            tar.close()
            return True
        except Exception as e:
            self.logger.error(f"Could not unpack tarfile [{file_name}]", datetime=datetime.utcnow())
            raise e

    def _convert_unpacked_to_netcdf4(self, download_folder):
        import cfgrib
        # A function that handles the many small GRIB files that were unpacked and formats those into NetCDF4
        grib_files = glob.glob(str(Path(download_folder).joinpath("HA40_N25_*_GB")))

        lats, lons = self._build_grid_block(grib_files[0])

        for grib_file in grib_files:
            time_prediction_made, predicted_hour = self._get_time_from_file(grib_file[len(download_folder) + 1:])
            cfg_file = cfgrib.FileStream(grib_file)
            file_dataset = None

            for cfg_message in cfg_file:
                # We skip any rotated grid data from the first file in each set of files. Only regular ll grids will do.
                if cfg_message["gridType"] == "regular_ll":
                    field_name, line_dataset = self._process_cfg_message_to_line_dataset(
                        cfg_message=cfg_message,
                        lats=lats,
                        lons=lons,
                        time_prediction_made=time_prediction_made,
                        predicted_hour=predicted_hour
                    )

                    if line_dataset is not None:
                        if file_dataset is None:
                            file_dataset = line_dataset
                        else:
                            file_dataset[field_name] = line_dataset[field_name]

            save_filename = Path(download_folder).joinpath(
                self.file_prefix
                + str(time_prediction_made.year)
                + str(time_prediction_made.month).zfill(2)
                + str(time_prediction_made.day).zfill(2)
                + "_"
                + str(time_prediction_made.hour).zfill(2)
                + "00_prediction_for_"
                + str(predicted_hour).zfill(2)
                + "00.nc"
            )

            file_dataset = file_dataset.unstack("coord")
            file_dataset.time.encoding["units"] = "hours since 2018-01-01"

            file_dataset.to_netcdf(path=save_filename, format="NETCDF4")
            self.logger.info(f"Saved dataset as {save_filename}")

    def _process_cfg_message_to_line_dataset(self, cfg_message, lats, lons, time_prediction_made, predicted_hour):
        # Function that parses a cfgrib message into an Xarray dataset.
        cfg_level_type = "_".join(re.findall("[A-Z][^A-Z]*", cfg_message["typeOfLevel"])).lower()
        cfg_level = cfg_message["level"]

        if cfg_message["parameterName"] in arome_factors:
            field_name = arome_factors[cfg_message["parameterName"]]

            if arome_factors[cfg_message["parameterName"]][0] == "_":
                field_name = cfg_message["stepType"] + field_name
        else:
            field_name = 'unknown_code_' + cfg_message["parameterName"]

        if cfg_level == 0 and cfg_level_type == 'above_ground':
            field_name = f"surface_{field_name}"
        else:
            field_name = f"{cfg_level}m_{cfg_level_type}_{field_name}"

        field_name = field_name.strip()

        field_values = np.reshape(cfg_message["values"], len(lats) * len(lons))

        data_dict = {field_name: (["time", "coord"], [field_values])}
        prediction_time = time_prediction_made + relativedelta(hours=predicted_hour)

        dataset_coords = {
            "prediction_moment": [time_prediction_made],
            "time": [prediction_time],
            "coord": pd.MultiIndex.from_product([lats, lons], names=["lat", "lon"]),
        }
        line_dataset = xr.Dataset(data_vars=data_dict, coords=dataset_coords)
        line_dataset.time.encoding["units"] = self.time_encoding
        return field_name, line_dataset

    @staticmethod
    def _get_time_from_file(file: str) -> (datetime, datetime):
        # Function that parses the time-span a file represents into the datetime the prediction was made
        # and the hour it predicts.
        year = int(file[9:13])
        month = int(file[13:15])
        day = int(file[15:17])
        hour = int(file[17:19])
        file_time = datetime(year=year, month=month, day=day, hour=hour)

        # hourly prediction datetime
        predictive_hour = int(file[-7:-5])

        return file_time, predictive_hour

    @staticmethod
    def _build_grid_block(file: str):
        import cfgrib
        cf_streamed_file = cfgrib.FileStream(file)

        line_to_use = None
        for cf_line in cf_streamed_file:
            # Make sure we don't pick up the rotated grid that exists in the first hourly file (0000) for each
            # prediction..
            if cf_line['gridType'] == 'regular_ll':
                line_to_use = cf_line
                break

        lat_first = float(line_to_use["latitudeOfFirstGridPointInDegrees"])
        lat_last = float(line_to_use["latitudeOfLastGridPointInDegrees"])

        lon_first = float(line_to_use["longitudeOfFirstGridPointInDegrees"])
        lon_last = float(line_to_use["longitudeOfLastGridPointInDegrees"])

        lat_step = float(line_to_use["jDirectionIncrement"])
        lon_step = float(line_to_use["iDirectionIncrement"])

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
        prediction_files = sorted(glob.glob(str(Path(download_folder).joinpath("AROME*.nc"))))

        ds = None

        for prediction_file in prediction_files:
            self.logger.info(f"Merging prediction file [{prediction_file}]")
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
            compressed_netcdf4_file.createDimension(name, len(dim) if not dim.isunlimited() else None)

        # Copy the global attributes
        compressed_netcdf4_file.setncatts({a: source_file.getncattr(a) for a in source_file.ncattrs()})

        # Create the variables in the file
        for name, var in source_file.variables.items():
            compressed_netcdf4_file.createVariable(name, var.dtype, var.dimensions, zlib=True)

            # Copy the variable attributes
            compressed_netcdf4_file.variables[name].setncatts({a: var.getncattr(a) for a in var.ncattrs()})

            # Copy the variables values (as 'f4' eventually)
            compressed_netcdf4_file.variables[name][:] = source_file.variables[name][:]

        # Save the file
        source_file.close()
        compressed_netcdf4_file.close()

        # Remove the uncompressed file
        self._safely_delete_file(save_file_name + "UC")

    def _empty_folder(self, download_folder):
        # Function that cleans up the temporary download folder
        self.logger.debug(f"Emptying up the folder [{download_folder}]", datetime=datetime.utcnow())
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
        len_filename_until_date = len(str(self.repository_folder.joinpath(self.file_prefix))) + 1

        for file_name in glob.glob(str(self.repository_folder.joinpath(self.file_prefix)) + "*.nc"):
            file_date = datetime(
                year=int(file_name[len_filename_until_date: len_filename_until_date + 4]),
                month=int(file_name[len_filename_until_date + 4: len_filename_until_date + 6]),
                day=int(file_name[len_filename_until_date + 6: len_filename_until_date + 8]),
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            if file_date < self.get_first_day_of_repo() or file_date > self.get_last_day_of_repo():
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
        self.logger.debug(f"Checking files in [{self.repository_folder}]")
        len_filename_until_date = len(str(self.repository_folder.joinpath(self.file_prefix))) + 1

        full_list_of_files = glob.glob(str(self.repository_folder.joinpath(self.file_prefix)) + "*.nc")
        list_of_filtered_files = []

        for file in full_list_of_files:
            file_date = datetime(
                year=int(file[len_filename_until_date: len_filename_until_date + 4]),
                month=int(file[len_filename_until_date + 4: len_filename_until_date + 6]),
                day=int(file[len_filename_until_date + 6: len_filename_until_date + 8]),
                hour=int(file[len_filename_until_date + 9: len_filename_until_date + 11]),
                minute=0,
                second=0,
                microsecond=0,
            )

            if start <= file_date <= end:
                # If the file is within the requested period, save it to the list of filtered files
                list_of_filtered_files.append(file)

        return list_of_filtered_files

    def get_grid_coordinates(self, coordinates: List[GeoPosition]) -> List[GeoPosition]:
        """ Rounds a list of GeoPositions to the resolution set through grid_resolution """
        return round_coordinates_to_wgs84_grid(coordinates, (0.023, 0.037), (49, 0))
