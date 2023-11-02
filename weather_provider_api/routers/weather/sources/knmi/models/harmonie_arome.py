#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" -- MODULE --

"""
import copy
from datetime import datetime, time, timedelta
from typing import List, Union

import xarray as xr
from loguru import logger

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.sources.knmi.client.arome_repository import HarmonieAromeRepository
from weather_provider_api.routers.weather.sources.knmi.knmi_factors import arome_factors
from weather_provider_api.routers.weather.utils.date_helpers import validate_begin_and_end
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class HarmonieAromeModel(WeatherModelBase):
    """A weather model that incorporates the 'KNMI - Harmonie Arome' weather dataset into the Weather Provider
     Libraries and API.

    'KNMI - Harmonie Arome' is a predictive model for the upcoming 48 hours that gets generated every 6 hours.
    """

    def __init__(self):
        # Pre-work
        super().__init__()
        self.id = "arome"
        logger.debug(f"Initializing weather model: {self.id}")

        # Setting the model
        self.repository = HarmonieAromeRepository()
        self.name = "harmonie_arome_cy_p1"
        self.version = "0.3"
        self.url = "ftp://data.knmi.nl/download/harmonie_arome_cy40_p1/0.2/"
        self.predictive = True
        self.time_step_size_minutes = 60
        self.num_time_steps = 48
        self.async_model = False
        self.dataset_name = "harmonie_arome_cy40_p1"
        self.dataset_version = "0.2"

        # Put up conversion settings
        si_conversion_dict = {
            k: {"name": k, "convert": lambda x: x} for k in arome_factors.values()
        }  # The default output format for Arome is SI
        self.to_si = si_conversion_dict

        # Human output conversion:
        self.to_human = copy.deepcopy(self.to_si)
        self.to_human["temperature"]["convert"] = self.kelvin_to_celsius

        # Initialization complete
        logger.debug(f'The Weather model "{self.id}" was successfully initialized')

    def get_weather(
        self,
        coords: List[GeoPosition],
        begin: datetime = None,
        end: datetime = None,
        weather_factors: List[str] = None,
    ) -> xr.Dataset:
        """Implementation of the WeatherModelBase get_weather function that fetches weather data and returns it as a
        Xarray DataSet.

        """
        # Handle possibly missing values for this model
        begin = begin or datetime.combine(datetime.today(), time.min)  # Fallback: start of today
        end = end or datetime.combine(datetime.today() + timedelta(days=1), time.max)  # Fallback: end of tomorrow

        # Validate the given timeframe
        valid_begin, valid_end = validate_begin_and_end(
            begin, end, self.repository.first_day_of_repo, self.repository.last_day_of_repo
        )

        # Gather the period from the repository
        weather_dataset = self.repository.gather_period(begin=valid_begin, end=valid_end, coordinates=coords)

        # Filter the requested factors
        translated_factors = []
        if weather_factors is not None:
            for factor in weather_factors:
                if factor in arome_factors.keys():
                    new_factor = arome_factors[factor]
                elif factor in arome_factors.values():
                    new_factor = factor
                else:
                    new_factor = None

                if new_factor is not None:
                    translated_factors.append(new_factor)

            for factor in weather_dataset.keys():
                if not any(item in factor for item in translated_factors):
                    weather_dataset = weather_dataset.drop(factor)

        return weather_dataset

    def is_async(self):
        return self.async_model

    def _request_weather_factors(self, factor_list: Union[List[str], None]) -> List[str]:
        """Implementation of the Weather Model Base function that returns a list of the known weather factors out of
        a given list for this model.

        """
        if not factor_list:
            return list(self.to_si.keys())

        validated_factors = []

        for factor in factor_list:
            factor_lowercase = factor.lower()

            if factor_lowercase in self.to_si:
                validated_factors.append(factor_lowercase)
            elif factor in self.to_si:
                validated_factors.append(factor)

        return list(set(validated_factors))
