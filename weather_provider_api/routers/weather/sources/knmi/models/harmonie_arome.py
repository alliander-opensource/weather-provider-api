#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""
    This module hold the Weather Model for the Harmonie Arome weather data set
"""

import copy
from datetime import datetime
from typing import List, Optional

import structlog
import xarray as xr

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.sources.knmi.client.arome_repository import AromeRepository
from weather_provider_api.routers.weather.sources.knmi.knmi_factors import arome_factors
from weather_provider_api.routers.weather.utils.date_helpers import validate_begin_and_end
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class AromeModel(WeatherModelBase):
    """
    A Weather Model that incorporates the:
        KNMI Harmonie Arome
    dataset into the Weather Provider API
    """

    def __init__(self):
        super().__init__()
        self.id = "arome"
        self.logger = structlog.get_logger(__name__)
        self.logger.debug(
            f"Initializing weather model [{self.id}]", datetime=datetime.utcnow()
        )

        self.repository = AromeRepository()

        self.name = "harmonie_arome_cy_p1"
        self.version = "0.3"
        self.url = "ftp://data.knmi.nl/download/harmonie_arome_cy40_p1/0.2/"
        self.predictive = True
        self.time_step_size_minutes = 60
        self.num_time_steps = 48
        self.async_model = False
        self.dataset_name = "harmonie_arome_cy40_p1"
        self.dataset_version = "0.2"

        si_conversion_dict = {
            k: {"name": k, "convert": lambda x: x} for k in arome_factors.values()
        }  # The default output format for Arome is SI
        self.to_si = si_conversion_dict

        # Human output conversion:
        self.to_human = copy.deepcopy(self.to_si)
        self.to_human["temperature"]["convert"] = self.kelvin_to_celsius

        self.logger.debug(
            f"Weather model [{self.id}] initialized successfully",
            datetime=datetime.utcnow(),
        )

    def get_weather(
        self,
        coords: List[GeoPosition],
        begin: Optional[datetime],
        end: Optional[datetime],
        weather_factors: List[str] = None,
    ) -> xr.Dataset:
        """
            The function that gathers and processes the requested Harmonie Arome weather data from the KNMI site
            and returns it as an Xarray Dataset.
            (This model uses the KNMI Data Platform for data acquisition using a repository)
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
            begin, end, self.repository.get_first_day_of_repo(), self.repository.get_last_day_of_repo()
        )

        ds = self.repository.gather_period(begin, end, coords)
        ds = ds.sel(
            prediction_moment=slice(begin, end)
        )  # Slice of any overflowing time-range

        return ds

    def is_async(self):
        return self.async_model

    def _request_weather_factors(self, factors: Optional[List[str]]) -> List[str]:
        # Implementation of the Base Weather Model function that returns a list of known weather factors for the model.
        if factors is None:
            return list(self.to_si.keys())

        new_factors = []

        for f in factors:
            f_up = f.upper()
            f_low = f.lower()

            if f_up in self.to_si:
                # KNMI daggegevens and uurgegevens (TD, TG, FHX, ...)
                new_factors.append(f_up)
            elif f_low in self.to_si:
                # Harmonie like (10v, mcc, nlwrs, ...)
                new_factors.append(f_low)
            elif f in self.to_si:
                new_factors.append(f)

        return list(set(new_factors))  # Cleanup any duplicate values and return
