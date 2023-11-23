#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" This module houses the repository class for the Actuele Waarnemingen Register. """
from datetime import datetime
from typing import List

import xarray as xr
from dateutil import tz
from dateutil.relativedelta import relativedelta
from loguru import logger

from weather_provider_api.routers.weather.repository.repository import (
    WeatherRepositoryBase,
)
from weather_provider_api.routers.weather.sources.knmi.utils import (
    download_actuele_waarnemingen_weather,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.grid_helpers import (
    round_coordinates_to_wgs84_grid,
)


class ActueleWaarnemingenRegisterRepository(WeatherRepositoryBase):
    """ """

    def _delete_files_outside_of_scope(self):
        logger.info(f"Deleting files outside of scope [{self.first_day_of_repo} - {self.last_day_of_repo}]")
        if self.filename.exists():
            current_data = xr.load_dataset(self.filename, engine="netcdf4")
            current_data = current_data.sel(time=slice(self.first_day_of_repo, self.last_day_of_repo))
            current_data.to_netcdf(self.filename, format="NETCDF4")

    def _get_file_list_for_period(self, start: datetime, end: datetime):
        return self.filename

    def __init__(self):
        # Pre-work
        super().__init__()

        self.repository_name = "KNMI Actuele Waarnemingen - 48 uur register"

        # Repository settings
        self.file_prefix = "ACTUEEL48"
        self.runtime_limit = 3 * 60  # Three minutes maximum runtime
        self.permanent_suffixes = []
        self.filename = self.repository_folder / f"{self.file_prefix}_register.nc"
        self.file_identifier_length = 8

        logger.debug(f"Initialized the [{self.repository_name}] repository")

    @property
    def repository_sub_folder(self):
        return "ACTUEEL48"  # not using self.file_prefix, because that may not exist the first time using this

    def _get_repo_sub_folder(self):
        return self.repository_sub_folder

    @property
    def first_day_of_repo(self) -> datetime:
        # Property to get the first moment of the repository as translated to the Dutch timezone.
        from_zone = tz.gettz("UTC")
        to_zone = tz.gettz("Europe/Amsterdam")

        first_day_of_repo = datetime.utcnow() - relativedelta(hours=48)  # 48 hours
        first_day_of_repo = first_day_of_repo.replace(tzinfo=from_zone)
        first_day_of_repo = first_day_of_repo.astimezone(to_zone)
        return first_day_of_repo.replace(tzinfo=None)

    @property
    def last_day_of_repo(self) -> datetime:
        # Property to get the last moment of the repository as translated to the Dutch timezone.
        from_zone = tz.gettz("UTC")
        to_zone = tz.gettz("Europe/Amsterdam")

        last_day_of_repo = datetime.utcnow()  # Right now
        last_day_of_repo = last_day_of_repo.replace(tzinfo=from_zone)
        last_day_of_repo = last_day_of_repo.astimezone(to_zone)

        return last_day_of_repo.replace(tzinfo=None)

    def update(self):
        """Implementation of the WeatherRepository update method

        Attempts to update the repository with the current data. For this repository, that means getting the current
         Actuele Waarnemingen output and storing it, while removing any data not within the scope of the repository.

        Returns:
            Nothing.

        """
        raw_weather_ds = download_actuele_waarnemingen_weather()
        time = datetime.utcnow().replace(second=0, microsecond=0)

        # Cleanup any old data
        self.cleanup()

        # Update the file
        self._update_file_with_new_data(new_data_ds=raw_weather_ds, update_moment=time)

    def _update_file_with_new_data(self, new_data_ds: xr.Dataset, update_moment: datetime):
        """This method updates any existing data file with new data or creates a new from scratch if needed, using the
         given dataset.

        Args:
            new_data_ds (xr.Dataset):   A Xarray Dataset holding the data to append / create the data file with.
            update_moment (datetime):   A datetime holding the moment of update. Note that this doesn't need to be the
                                         moment that the data is from.

        Returns:
            Nothing. The file is just updated.

        """
        # Opening the file:
        if self.filename.exists():
            stored_data_ds = xr.load_dataset(self.filename, engine="netcdf4")
        else:
            stored_data_ds = None

        logger.info(
            f"Storing data at [{update_moment.strftime('%m-%d-%Y %H:%M:%S')}] for "
            f"[{new_data_ds.isel(STN=0, time=0)['time'].values}]"
        )
        if stored_data_ds is None:
            new_data_ds.to_netcdf(self.filename, format="NETCDF4")
        else:
            # Check if time not already in system
            try:
                new_stored_data_ds = xr.merge([new_data_ds, stored_data_ds])

                new_stored_data_ds.to_netcdf(self.filename, format="NETCDF4")
            except ValueError as value_error:
                logger.error(f"Could not update file: {value_error}")

    def get_24_hour_registry_for_station(self, station: int) -> xr.Dataset:
        """This method obtains the last 24 hours of data of Actuele Waarnemingen and returns it for single station.

        Args:
            station (int):  An integer representing the station to gather data for

        Returns:
            xr.Dataset: A Xarray Dataset holding last 24 hours of data for the requested station

        """
        stored_data_ds = xr.load_dataset(self.filename, engine="netcdf4")
        return stored_data_ds.sel(
            STN=station,
            time=slice(self.first_day_of_repo + relativedelta(days=1), self.last_day_of_repo),
        )

    def get_48_hour_registry_for_station(self, station: int) -> xr.Dataset:
        """This method obtains the last 48 hours of data of Actuele Waarnemingen and returns it for single station.

        Args:
            station (int):  An integer representing the station to gather data for

        Returns:
            xr.Dataset: A Xarray Dataset holding last 48 hours of data for the requested station

        """
        stored_data_ds = xr.load_dataset(self.filename, engine="netcdf4")
        stored_data_ds = stored_data_ds.sel(
            STN=station,
            time=slice(self.first_day_of_repo, self.last_day_of_repo),
        )
        return stored_data_ds

    def get_grid_coordinates(self, coordinates: List[GeoPosition]) -> List[GeoPosition]:
        """Rounds a list of GeoPositions to the resolution set through grid_resolution"""
        return round_coordinates_to_wgs84_grid(coordinates, (0.023, 0.037), (49, 0))
