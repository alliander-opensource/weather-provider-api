#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" KNMI current weather data aggregate fetcher.
"""
import copy
from datetime import datetime
from typing import List, Optional

import numpy as np
import xarray as xr
from dateutil.relativedelta import relativedelta

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.sources.knmi.client.actuele_waarnemingen_register_repository import (
    ActueleWaarnemingenRegisterRepository,
)
from weather_provider_api.routers.weather.sources.knmi.stations import stations_actual
from weather_provider_api.routers.weather.sources.knmi.utils import (
    find_closest_stn_list,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.pandas_helpers import coords_to_pd_index


class ActueleWaarnemingenRegisterModel(WeatherModelBase):
    """
    A Weather model aimed at accessing a 24-hour register for the "KNMi Actuele Waarnemingen" dataset.
    """

    def is_async(self):
        return self.async_model

    def __init__(self):
        super().__init__()
        self.id = "waarnemingen_register"
        self.name = "KNMI Actuele Waarnemingen - 48 uur register"
        self.version = ""
        self.url = "https://www.knmi.nl/nederland-nu/weer/waarnemingen"
        self.predictive = False
        self.time_step_size_minutes = 10
        self.num_time_steps = 12
        self.description = "48 Hour register for current weather observations. Updated every 10 minutes."
        self.async_model = False
        self.repository = ActueleWaarnemingenRegisterRepository()

        self.to_si = {
            "weather_description": {
                "name": "weather_description",
                "convert": self.no_conversion,
            },
            "temperature": {"convert": self.celsius_to_kelvin},
            "humidity": {"convert": self.percentage_to_frac},
            "wind_direction": {"convert": self.dutch_wind_direction_to_degrees},
            "wind_speed": {"convert": self.no_conversion},  # m/s
            "visibility": {"convert": self.no_conversion},  # m
            "air_pressure": {"convert": lambda x: x * 100},  # hPa to Pa
        }
        self.to_human = copy.deepcopy(self.to_si)
        self.to_human["temperature"]["convert"] = self.no_conversion  # C

        self.human_to_model_specific = self._create_reverse_lookup(self.to_si)

    def get_weather(
        self,
        coords: List[GeoPosition],
        begin: Optional[np.datetime64],
        end: Optional[np.datetime64],
        weather_factors: List[str] = None,
    ) -> xr.Dataset:
        """
        The function that gathers and processes the requested Actuele Waarnemingen Register weather data from the
        48-hour register and returns it as a Xarray Dataset.
        (The register for this model interprets directly from an HTML page, but the information is also available from
        the data platform. Due to it being rather impractically handled, we stick to the site for now.)

        Args:
            coords:             A list of GeoPositions containing the locations the data is requested for.
            begin:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            weather_factors:    A list of weather factors to request data for (in string format)

        Returns:
            An Xarray Dataset containing the weather data for the requested period, locations and factors.

        NOTES:
            As this model only return the current weather data the 'begin' and 'end' values are not actually used.
        """
        updated_weather_factors = self._request_weather_factors(weather_factors)
        coords_stn, _, _ = find_closest_stn_list(stations_actual, coords)

        now = datetime.utcnow()
        if now - relativedelta(days=1) > begin:
            raw_ds = self.repository.get_48_hour_registry_for_station(station=coords_stn)
        else:
            raw_ds = self.repository.get_24_hour_registry_for_station(station=coords_stn)

        data_dictionary = {
            var_name: (["time", "coord"], var.values)
            for var_name, var in raw_ds.data_vars.items()
            if var_name in updated_weather_factors and var_name not in ["lat", "lon"]
        }

        timeline = raw_ds.coords["time"].values

        output_ds = xr.Dataset(
            data_vars=data_dictionary,
            coords={"time": timeline, "coord": coords_to_pd_index(coords)},
        )
        output_ds = output_ds.unstack("coord")
        return output_ds

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
