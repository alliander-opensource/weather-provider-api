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
from typing import List, Tuple

import cfgrib
import numpy as np
import pandas as pd
import pytz
import xarray as xr
from dateutil.relativedelta import relativedelta
from loguru import logger

from weather_provider_api.routers.weather.repository.repository import (
    RepositoryUpdateResult,
    WeatherRepositoryBase,
)
from weather_provider_api.routers.weather.sources.knmi.client.knmi_downloader import (
    KNMIDownloader,
)
from weather_provider_api.routers.weather.sources.knmi.knmi_factors import arome_factors
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.grid_helpers import (
    round_coordinates_to_wgs84_grid,
)


class HarmonieAromeRepository(WeatherRepositoryBase):
    """The Weather Repository class for the 'KNMI - Harmonie Arome' dataset"""

    def __init__(self):
        # Pre-work
        super().__init__()

        self.repository_name = "KNMI Harmonie (Arome)"
        logger.debug(f"Initialized {self.repository_name} repository")

        # Repository settings
        self.file_prefix = "AROME"
        self.runtime_limit = 60 * 60 * 3  # 3 hours maximum runtime
        self.permanent_suffixes = ["0000", "0600", "1200", "1800"]
        self.dataset_name = "harmonie_arome_cy40_p1"
        self.dataset_version = "0.2"
        self.file_identifier_length = 13
        self.time_encoding = "hours since 2018-01-01"  # Used to keep values usable for at least the upcoming decennium

        # Verify if cfgrib is properly installed
        try:
            import cfgrib
        except RuntimeError as e:
            logger.warning(f"CFGRIB could not properly be initialized: {e}")
            logger.warning(
                "Due to problems with CFGRIB, this repository will only be able to access existing "
                "data. The repository will not be able to update"
            )

    @property
    def repository_sub_folder(self):
        return "AROME"

    def _get_repo_sub_folder(self):
        return self.repository_sub_folder

    @property
    def first_day_of_repo(self):
        first_day_of_repo = datetime.utcnow() - relativedelta(years=3)  # Three years back
        first_day_of_repo = first_day_of_repo.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # Start of day
        return first_day_of_repo

    @property
    def last_day_of_repo(self):
        last_day_of_repo = datetime.utcnow().replace(minute=0, second=0, microsecond=0)  # Start of today
        return last_day_of_repo

    def update(self):
        """The implementation of the WeatherRepository update function.

        This function gathers any new 'KNMI - Harmonie Arome' files and processes them into the repository. A
         RepositoryUpdateResult object if returned indication success, time-out or failure.

        """
        # Stop if cfgrib wasn't added into the system modules during boot.
        if "cfgrib" not in sys.modules:
            logger.error('CANNOT PERFORM UPDATE: No valid "cfgrib" installation available.')
            logger.info('Please properly install "cfgrib" and restart the system to enable updates.')
            quit()

        # Cleanup the repository
        self.cleanup()

        logger.info(f"KNMI Arome Update - Storage in: {self.repository_folder} ")

        # Configure initial settings for the update
        start_of_update = datetime.utcnow()
        no_of_items_processed = 0
        average_seconds_per_item = 1500  # Assuming 25 minutes of processing time per month for the first item
        forced_end_of_update = start_of_update + relativedelta(seconds=self.runtime_limit)

        logger.info(f"Update of [{self.repository_name}] started")
        logger.info(f"- A forced end time of [{forced_end_of_update}] was set.")

        prediction_to_evaluate = self.get_most_recent_prediction_moment
        download_folder = Path(tempfile.gettempdir()).joinpath(self.dataset_name)
        knmi_downloader = KNMIDownloader(self.dataset_name, self.dataset_version, str(download_folder), True)
        files_in_dataset = {item["filename"]: item["size"] for item in knmi_downloader.get_all_available_files()}

        while prediction_to_evaluate >= self.first_day_of_repo:
            if no_of_items_processed != 0:
                average_seconds_per_item = (datetime.utcnow() - start_of_update).total_seconds() / no_of_items_processed

            if forced_end_of_update < (datetime.utcnow() + relativedelta(seconds=average_seconds_per_item)):
                logger.info(f"- Not enough time left to update before [{forced_end_of_update}]")
                logger.info(f"Update of [{self.repository_name}] ended...")
                return RepositoryUpdateResult.timed_out

            if not self._prediction_already_available(prediction_to_evaluate):
                logger.debug(f"- Gathering the prediction for: {prediction_to_evaluate}")
                file_to_download = (
                    f"harm40_v1_p1_{prediction_to_evaluate.year}"
                    f"{str(prediction_to_evaluate.month).zfill(2)}"
                    f"{str(prediction_to_evaluate.day).zfill(2)}"
                    f"{str(prediction_to_evaluate.hour).zfill(2)}.tar"
                )

                if file_to_download in files_in_dataset.keys():
                    # File exists
                    knmi_downloader.download_specific_file(file_to_download, files_in_dataset[file_to_download])
                    self._process_downloaded_file(download_folder, file_to_download, prediction_to_evaluate)
                    no_of_items_processed += 1
                else:
                    logger.info(
                        f"The expected file [{file_to_download}] was not found within the KNMI dataset. "
                        f"Moving on to the next file!"
                    )
            else:
                logger.debug(f"The prediction for [{prediction_to_evaluate}] is already stored in the repository.")

            prediction_to_evaluate -= relativedelta(hours=6)

        logger.info(f"Update of [{self.repository_name}] ended...")
        return RepositoryUpdateResult.completed

    def _prediction_already_available(self, prediction_moment: datetime):
        """Function to evaluate if a prediction is already available within the repository."""
        if self.repository_folder.joinpath(
            f"{self.file_prefix}_{prediction_moment.year}{str(prediction_moment.month).zfill(2)}"
            f"{str(prediction_moment.day).zfill(2)}_{str(prediction_moment.hour).zfill(2)}00.nc"
        ).exists():
            return True

        return False

    def _process_downloaded_file(self, download_folder: Path, filename: str, prediction_time: datetime):
        """The function that processes a number of downloaded files into repository files."""
        stage = "Started unpacking files.."
        try:
            self._unpack_downloaded_file(download_folder, filename)
            stage = "Files were unpacked"
            self._convert_unpacked_data_to_netcdf4_files(download_folder, prediction_time)
            stage = "Data was converted to NetCDF4"
            self._fuse_hourly_netcdf4_files(download_folder, prediction_time)
            stage = "NetCDF4 files were properly fused together"
            self._clear_temp_folder(download_folder)
        except Exception as e:
            logger.warning(f"Processing did not get past stage: {stage}")
            logger.warning(f"The downloaded data could not be properly downloaded: {e}")

    @staticmethod
    def _clear_temp_folder(download_folder: Path):
        """A function that cleans up the temporary download folder to prevent issues with partially written files."""
        logger.debug(f"Emptying the download folder: {download_folder}")
        for existing_file in glob.glob(f"{download_folder}*.*"):
            try:
                # Try to delete:
                Path(existing_file).unlink()
            except Exception as e:
                logger.info(f"An error occurred while deleting the file [{existing_file}]: {e}")
                logger.warning("There may be issues while updating using a file with an identical name...")

    @staticmethod
    def _unpack_downloaded_file(download_folder: Path, file_name: str):
        """The function that unpacks downloaded files to prediction files."""
        logger.info(f"Unpacking file: {file_name}")
        try:
            tar_file = tarfile.open(download_folder.joinpath(file_name))
            tar_file.extractall(path=download_folder)
            tar_file.close()
        except Exception as e:
            logger.error(f"The tarfile [{file_name}] could not be unpacked!")
            raise e

    def _convert_unpacked_data_to_netcdf4_files(self, download_folder: Path, prediction_time: datetime):
        """This function converts any unpacked data files into NetCDF4 files"""
        try:
            import cfgrib

            logger.debug("Import of cfgrib was successful")
        except RuntimeError as e:
            logger.error("CFGRIB was not properly installed. Cannot access GRIB files.")
            raise e

        grib_files_available = glob.glob(
            str(download_folder.joinpath(f'HA40_N25_{prediction_time.strftime("%Y%m%d%H")}00_*_GB'))
        )

        for grib_file in grib_files_available:
            logger.debug(f"Processing GRIB file: {grib_file}")
            self._convert_grib_file_to_NetCDF(Path(grib_file))

        logger.info("All Partial datasets were successfully processed.")

    def _convert_grib_file_to_NetCDF(self, grib_file: Path):
        """A function that converts a Harmonie Arome GRIB-file into a NetCDF4 file

        Args:
            grib_file (Path):   The Path to the GRIB file to convert

        Returns:
            Nothing

        """
        prediction_moment, predicted_hour = self._get_times_from_filename(grib_file.name)
        grib_filestream = cfgrib.FileStream(str(grib_file))
        file_dataset = xr.Dataset()

        for item in grib_filestream.items():
            grib_message = item[1]
            # We skip the rotated grid data of the first file in each file-set and only process the regular_ll grids.
            if grib_message["gridType"] == "regular_ll":
                (field_name, message_dataset,) = self._process_grib_message_to_message_dataset(
                    grib_message=grib_message,
                    prediction_moment=prediction_moment,
                    predicted_hour=predicted_hour,
                )
                if message_dataset:
                    if not file_dataset:
                        file_dataset = message_dataset
                    else:
                        file_dataset[field_name] = message_dataset[field_name]

        filename_to_save_to = Path(grib_file.parents[0]).joinpath(
            f"{self.file_prefix}_{prediction_moment.year}{str(prediction_moment.month).zfill(2)}"
            f"{str(prediction_moment.day).zfill(2)}_{str(prediction_moment.hour).zfill(2)}"
            f"00_prediction_for_{str(predicted_hour).zfill(2)}00.nc"
        )

        file_dataset = file_dataset.unstack("coord")
        file_dataset.time.encoding["units"] = "hours since 2018-01-01"

        file_dataset.to_netcdf(path=filename_to_save_to, format="NETCDF4")
        logger.info(f"Saved partial dataset as: {filename_to_save_to}")

    def _process_grib_message_to_message_dataset(
        self,
        grib_message: cfgrib.Message,
        prediction_moment: datetime,
        predicted_hour: int,
    ) -> (str, xr.Dataset):
        """

        Args:
            grib_message (grib.Message):    A GRIB message holding the data to process
            prediction_moment (datetime):   The datetime moment the data was generated
            predicted_hour (int):           The hour it is predicting

        Returns:
            (str, xarray.Dataset): A string holding the parameter name and a Xarray Dataset holding the data that was
            converted a dataset.

        """
        # Gather the message's level type and the level it was set to
        msg_level_type = "_".join(re.findall("[A-Z][^A-Z]*", grib_message["typeOfLevel"])).lower()
        msg_level = grib_message["level"]

        # Process the supported factors
        parameter_name = grib_message["parameterName"]
        if parameter_name in arome_factors:
            field_name = arome_factors[parameter_name]

            if arome_factors[parameter_name][0] == "_":
                # Add level unit to the name if needed
                field_name = f'{grib_message["stepType"]}{field_name}'
        else:
            field_name = f'unknown_code_{grib_message["parameterName"]}'

        # Add level information
        if msg_level == 0 and msg_level_type == "above_ground":
            field_name = f"surface_{field_name}"
        else:
            field_name = f"{msg_level}m_{msg_level_type}_{field_name}"

        # Prepare data for dataset creation
        field_name = field_name.strip()  # Strip any excess spaces
        lats, lons = self._build_lat_lon_grid(grib_message)  # Get the dimensions of the message
        field_values = np.reshape(grib_message["values"], len(lats) * len(lons))

        data_dict = {field_name: (["time", "coord"], [field_values])}
        predicted_moment = prediction_moment + relativedelta(hours=predicted_hour)

        dataset_coords = {
            "time_of_prediction": [prediction_moment],
            "time": [predicted_moment],
            "coord": pd.MultiIndex.from_product([lats, lons], names=["lat", "lon"]),
        }

        message_dataset = xr.Dataset(data_vars=data_dict, coords=dataset_coords)
        message_dataset.time.encoding["units"] = self.time_encoding

        return field_name, message_dataset

    @property
    def get_most_recent_prediction_moment(self):
        """Return the most recent prediction moment, based the current time in the Netherlands

        Returns:
            A datetime holding the most recent available prediction moment

        """
        knmi_lag_time = 5  # There is a known 5-hour calculation lag to take into account

        # Determine the current CET time (the KNMI works from the Netherlands, and this project from UTC)
        time_cet = self.last_day_of_repo.astimezone(pytz.timezone("Europe/Amsterdam"))
        time_cet += time_cet.utcoffset()  # We add the UTC offset to change the actual values to those hours
        time_cet = time_cet.replace(tzinfo=None, microsecond=0)  # Finish formatting

        time_cet -= relativedelta(hours=knmi_lag_time)  # Subtract the KNMI lag
        rounded_hour = (time_cet.hour // 6) * 6  # Get the nearest preceding hours divisible by six
        time_cet = time_cet.replace(hour=rounded_hour, minute=0, second=0)
        return time_cet

    def _fuse_hourly_netcdf4_files(self, download_folder: Path, prediction_moment: datetime):
        """

        Args:
            download_folder:
            prediction_moment:

        Returns:

        """
        logger.info(f"Starting merge of all files for: {prediction_moment}")
        existing_prediction_files = sorted(glob.glob(str(Path(download_folder).joinpath(f"{self.file_prefix}*.nc"))))

        fused_dataset = None

        for prediction_file in existing_prediction_files:
            logger.debug(f"- Starting merge of: {prediction_file}")
            with xr.open_dataset(prediction_file) as prediction_file_dataset:
                prediction_file_dataset.load()
                if not fused_dataset:
                    fused_dataset = prediction_file_dataset
                else:
                    fused_dataset = xr.merge([fused_dataset, prediction_file_dataset], compat="override")

        filename_to_save_to = self.repository_folder.joinpath(
            f"{self.file_prefix}_{prediction_moment.year}{str(prediction_moment.month).zfill(2)}"
            f"{str(prediction_moment.day).zfill(2)}_{str(prediction_moment.hour).zfill(2)}00.nc"
        )

        logger.debug(f"- Saving prediction [{prediction_moment}] to: {filename_to_save_to}")

        encoding = {v: {"zlib": True, "complevel": 4} for v in fused_dataset.variables}
        fused_dataset.to_netcdf(filename_to_save_to, format="NETCDF4", engine="netcdf4", encoding=encoding)

    @staticmethod
    def _build_lat_lon_grid(grib_message: cfgrib.Message) -> Tuple[List[float], List[float]]:
        """This function uses an existing GRIB file to extract the dimensions of the 'regular_ll' grid and format
         those into a list of latitudes and a list of longitudes that together make up the grid.

        Args:
            grib_message:  The GRIB file to use to

        Returns:
            Tuple[List[float], List[float]]: Two lists of float values, the first holding latitudes, and the second
                                              longitudes

        """
        # Try to import cfgrib and raise an error if it isn't properly installed.
        # Set the boundaries
        minimum_latitude = float(grib_message["latitudeOfFirstGridPointInDegrees"])
        maximum_latitude = float(grib_message["latitudeOfLastGridPointInDegrees"])

        minimum_longitude = float(grib_message["longitudeOfFirstGridPointInDegrees"])
        maximum_longitude = float(grib_message["longitudeOfLastGridPointInDegrees"])

        # And the step value needed to get all the inbetween values
        step_for_latitude = int(grib_message["jDirectionIncrement"])
        step_for_longitude = int(grib_message["iDirectionIncrement"])

        # Build the lists
        latitudes = list(
            range(  # We add the step-value to the max-value to include it itself.
                int(minimum_latitude * 1_000),
                int(maximum_latitude * 1_000 + step_for_latitude),
                step_for_latitude,
            )
        )
        longitudes = list(
            range(  # We add the step-value to the max-value to include it itself.
                int(minimum_longitude * 1_000),
                int(maximum_longitude * 1_000 + step_for_longitude),
                step_for_longitude,
            )
        )

        latitudes = [x / 1_000 for x in latitudes]
        longitudes = [y / 1_000 for y in longitudes]

        return latitudes, longitudes

    @staticmethod
    def _get_times_from_filename(filename: str) -> Tuple[datetime, int]:
        """This function extracts the timeframe a file represents from its name and translates that into the datetime
         that the prediction was made, and the exact hour it represents of that prediction.

        Args:
            filename:   The filename to parse

        Returns:
            A datetime and an int value indicating the prediction datetime and the predicted hour respectively

        """
        try:
            prediction_year = int(filename[9:13])
            prediction_month = int(filename[13:15])
            prediction_day = int(filename[15:17])
            prediction_hour = int(filename[17:19])

            predicted_hour = int(filename[-7:-5])
        except Exception as e:
            raise ValueError(f"Could not properly obtain the prediction from the title of the file: {filename} [{e}]")

        prediction_moment = datetime(
            year=prediction_year,
            month=prediction_month,
            day=prediction_day,
            hour=prediction_hour,
        )
        logger.debug(
            f"File [{filename}] was parsed to prediction moment and hour: [{prediction_moment}],[{predicted_hour}]"
        )
        return prediction_moment, predicted_hour

    def _delete_files_outside_of_scope(self):
        """The function that delete all out-of-scope files.

        This means that any file that does no longer exist within scope (either by existing before it, or by existing
         past it) will be removed.

        Returns:
            Nothing.

        Raises:


        """
        counter_until_date_in_filename = len(str(self.repository_folder.joinpath(self.file_prefix))) + 1

        for file_name in glob.glob(f"{self.repository_folder.joinpath(self.file_prefix)}*.nc"):
            file_date = datetime(
                year=int(file_name[counter_until_date_in_filename : counter_until_date_in_filename + 4]),
                month=int(file_name[counter_until_date_in_filename + 4 : counter_until_date_in_filename + 6]),
                day=int(file_name[counter_until_date_in_filename + 6 : counter_until_date_in_filename + 8]),
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ).date()

            if file_date < self.first_day_of_repo.date() or file_date > self.last_day_of_repo.date():
                logger.debug(f"The current scope is [{self.first_day_of_repo.date()}-{self.last_day_of_repo.date()}]")
                logger.debug(f"The file [{file_name}] resolved to [{file_date}], which lies out of scope.")
                logger.debug(f"The file [{file_name}] will therefor be deleted.")

                self._safely_delete_file(file_name)

    def _get_file_list_for_period(self, start: datetime, end: datetime) -> List[Path]:
        """This function creates a list of the files associated with the requested timeframe.

        Args:
            start (datetime):    The start of the timeframe to use
            end (datetime):       The end of the timeframe to use

        Returns:
            List[Path]: A list of the files associated with the given timeframe

        """
        logger.debug(f"Finding files for the timeframe: [({start})-({end})]")
        logger.debug(f"Searching folder: [{self.repository_folder}]")
        counter_until_date_in_filename = len(str(self.repository_folder.joinpath(self.file_prefix))) + 1

        list_of_all_netcdf4_files_in_repo = glob.glob(str(self.repository_folder.joinpath(f"{self.file_prefix}*.nc")))
        list_of_files_in_timeframe = []

        for file_name in list_of_all_netcdf4_files_in_repo:
            file_date = datetime(
                year=int(file_name[counter_until_date_in_filename : counter_until_date_in_filename + 4]),
                month=int(file_name[counter_until_date_in_filename + 4 : counter_until_date_in_filename + 6]),
                day=int(file_name[counter_until_date_in_filename + 6 : counter_until_date_in_filename + 8]),
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            ).date()

            # Add to the list if within the timeframe
            if start.date() <= file_date <= end.date():
                list_of_files_in_timeframe.append(Path(file_name))

        return list_of_files_in_timeframe

    def get_grid_coordinates(self, coordinates: List[GeoPosition]) -> List[GeoPosition]:
        """Rounds a list of GeoPositions to the resolution set through grid_resolution"""
        return round_coordinates_to_wgs84_grid(coordinates, (0.023, 0.037), (49, 0))
