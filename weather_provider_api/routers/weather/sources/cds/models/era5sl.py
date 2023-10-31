#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""
    CDS - ERA5 Single Levels Weather data Model
"""
import copy
from datetime import datetime
from typing import List, Optional

import numpy as np
import xarray as xr
from loguru import logger

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.sources.cds.client.era5sl_repository import ERA5SLRepository
from weather_provider_api.routers.weather.sources.cds.factors import era5sl_factors
from weather_provider_api.routers.weather.utils.date_helpers import validate_begin_and_end
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class ERA5SLModel(WeatherModelBase):
    """
    A Weather Model that incorporates the:
        ERA5 hourly data on single levels from 1979 to present
    dataset into the Weather Provider API
    """

    def __init__(self):
        super().__init__()
        self.id = "era5sl"
        logger.debug(f"Initializing weather model [{self.id}]")

        self.name = "CDS ERA5 - Hourly data on single levels from 1979 to the present"

        self.version = "0.3"
        self.url = "https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-single-levels?tab=overview"
        self.predictive = False
        self.description = (
            "Hourly weather measurements. Can be returned for a specified period. The number of "
            "measurements returned depends on this period selection."
        )
        self.async_model = False

        self.time_step_size_minutes = 60
        self.num_time_steps = 0

        self.repository = ERA5SLRepository()

        # Set up Conversion Dictionary
        si_conversion_dict = {
            k: {"name": k, "convert": lambda x: x} for k in era5sl_factors.values()
        }  # The default output format for ERA5SL is already SI
        self.to_si = si_conversion_dict

        # Human output conversion:
        self.to_human = copy.deepcopy(self.to_si)
        self.to_human["sea_surface_temperature"]["convert"] = self.kelvin_to_celsius
        self.to_human["soil_temperature_level_1"]["convert"] = self.kelvin_to_celsius
        self.to_human["soil_temperature_level_2"]["convert"] = self.kelvin_to_celsius
        self.to_human["soil_temperature_level_3"]["convert"] = self.kelvin_to_celsius
        self.to_human["soil_temperature_level_4"]["convert"] = self.kelvin_to_celsius
        self.to_human["2m_temperature"]["convert"] = self.kelvin_to_celsius

        logger.debug(f"Weather model [{self.id}] initialized successfully")

    def is_async(self):
        """Returns the async model status"""
        return self.async_model

    def get_weather(
        self,
        coords: List[GeoPosition],
        begin: datetime,
        end: datetime,
        weather_factors: List[str] = None,
    ) -> xr.Dataset:
        """
            The function that gathers and processes the requested ERA5 Single Levels weather data from the repository
            and returns it as a Xarray Dataset.
        Args:
            coords:             A list of GeoPositions containing the locations the data is requested for.
            begin:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            weather_factors:    A list of weather factors to request data for (in string format)
        Returns:
            An Xarray Dataset containing the weather data for the requested period, locations and factors.
        """

        # Test and account for invalid datetime timeframes or input
        begin, end = validate_begin_and_end(
            begin,
            end,
            self.repository.first_day_of_repo,
            self.repository.last_day_of_repo,
        )

        # Validate the requested weather factors:
        validated_factors = self._validate_weather_factors(weather_factors)

        ds = self._fill_dataset_with_data(coords, begin, end, validated_factors)
        return ds

    @staticmethod
    def _validate_weather_factors(weather_factors: List[str]) -> List[str]:
        """
            A function that validates a list of weather factors to that of the dataset in the repository.
            Existing factors will be kept, non-existing removed, and if the list is empty the full set for the dataset
            will be used.
        Args:
            weather_factors:    A list of weather factors to validate (in string format)
        Returns:
            A list of weather factors (in string format) only factors that match those of the ERA5SL dataset.
        """
        if weather_factors is None:
            weather_factors = [era5sl_factors[x] for x in list(era5sl_factors.keys())]

        # Lookup using the generic long name
        weather_factors_long_names = [x for x in weather_factors if x in era5sl_factors.values()]
        # Lookup using the CDS' own short name
        weather_factors_short_names = [era5sl_factors[x] for x in weather_factors if x in era5sl_factors.keys()]

        # Merge the results
        weather_factors = weather_factors_long_names + weather_factors_short_names

        # If nothing useful was found, just return everything
        return weather_factors

    @staticmethod
    def _get_list_of_factors_to_drop(factors: List[str]) -> List[str]:
        # A small function that that compares a list of factors to keep with the full list, to make a list of factors
        # to drop from a full set.
        to_drop = [x for x in era5sl_factors.values() if x not in factors]
        logger.debug("Dropping the following factors for the request: " + str(to_drop))
        return to_drop

    def _fill_dataset_with_data(
        self,
        era5sl_coordinates: List[GeoPosition],
        begin: datetime,
        end: datetime,
        validated_factors: List[str],
    ) -> xr.Dataset:
        """
            A function that fills a dataset with ERA5SL weather data from the repository, based on the requested
            coordinates and period, and removes any not-requested weather factors from the output.
        Args:
            era5sl_coordinates:     A list of GeoPositions containing the locations to be gathered from the repository.
            begin:                  A datetime containing the starting moment for the period to gather.
            end:                    A datetime containing the end moment for the period to gather.
            validated_factors:      A list of valid ERA5SL factors wanted for the result.
        Returns:
            An Xarray Dataset containing the weather data requested.
        """
        # Gather a dataset with the proper period and coordinates
        ds = self.repository.gather_period(begin, end, era5sl_coordinates)

        ds = ds.sel(time=slice(np.datetime64(begin), np.datetime64(end)))

        # Drop excess weather factors
        ds = ds.drop_vars(self._get_list_of_factors_to_drop(validated_factors))
        return ds

    def _request_weather_factors(self, factors: Optional[List[str]]) -> List[str]:
        # Implementation of the Base Weather Model function that returns a list of known weather factors for the model.
        if factors is None:
            return list(self.to_si.keys())

        new_factors = []

        for f in factors:
            f_low = f.lower()

            if f_low in self.to_si:
                new_factors.append(f_low)

        return list(set(new_factors))  # Cleanup any duplicate values and return
