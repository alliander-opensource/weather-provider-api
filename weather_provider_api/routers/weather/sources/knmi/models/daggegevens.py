#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""
    KNMI day models data fetcher.
"""

import copy
import json
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
import requests
import xarray as xr
from dateutil.relativedelta import relativedelta
from loguru import logger

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.sources.knmi.stations import stations_history
from weather_provider_api.routers.weather.sources.knmi.utils import (
    find_closest_stn_list,
)
from weather_provider_api.routers.weather.utils.date_helpers import (
    validate_begin_and_end,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.pandas_helpers import coords_to_pd_index


class DagGegevensModel(WeatherModelBase):
    """
    A Weather Model that incorporates the:
        KNMI Daggegevens
    dataset into the Weather Provider API
    """

    def __init__(self):
        super().__init__()
        self.id = "daggegevens"
        self.name = "KNMI daggegevens"
        self.version = ""
        self.url = "https://daggegevens.knmi.nl/klimatologie/daggegevens"
        self.predictive = False
        self.time_step_size_minutes = 1440
        self.num_time_steps = 0
        self.description = (
            "Daily weather measurements. Can be returned for a specified period. "
            "The number of measurements returned depends on this period selection."
        )
        self.async_model = False
        self.download_url = "https://daggegevens.knmi.nl/klimatologie/daggegevens"

        self.to_si = {
            "DDVEC": {"name": "wind_direction", "convert": self.no_conversion},
            "FHVEC": {"convert": self.normalize_tenths},  # 0.1 m/s -> m/s
            "FG": {
                "name": "wind_speed",
                "convert": self.normalize_tenths,
            },  # 0.1 m/s -> m/s
            "FHX": {
                "name": "wind_speed_max",
                "convert": self.normalize_tenths,
            },  # 0.1 m/s -> m/s
            "FHXH": {"name": "wind_speed_max_hour", "convert": self.no_conversion},
            "FHN": {
                "name": "wind_speed_min",
                "convert": self.normalize_tenths,
            },  # 0.1 m/s -> m/s
            "FHNH": {"name": "wind_speed_min_hour", "convert": self.no_conversion},
            "FXX": {
                "name": "wind_gust_max",
                "convert": self.normalize_tenths,
            },  # 0.1 m/s -> m/s
            "FXXH": {"name": "wind_gust_max_hour", "convert": self.no_conversion},
            "TG": {
                "name": "temperature",
                "convert": self.tenth_celsius_to_kelvin,  # 0.1 degree C -> Kelvin
            },
            "TN": {
                "name": "temperature_min",
                "convert": self.tenth_celsius_to_kelvin,  # 0.1 degree C -> Kelvin
            },
            "TNH": {"name": "temperature_min_hour", "convert": self.no_conversion},
            "TX": {
                "name": "temperature_max",
                "convert": self.tenth_celsius_to_kelvin,  # 0.1 degree C -> Kelvin
            },
            "TXH": {"name": "temperature_max_hour", "convert": self.no_conversion},
            "T10N": {"convert": self.tenth_celsius_to_kelvin},  # 0.1 degree C -> Kelvin
            "T10NH": {"convert": self.no_conversion},
            "SQ": {
                "name": "sunlight_duration",
                "convert": self.normalize_tenths,
            },  # 0.1 hour -> hour
            "SP": {
                "name": "percentage_of_max_possible_sunlight_duration",
                "convert": self.percentage_to_frac,
            },  # % -> fraction
            "Q": {
                "name": "global_radiation",
                "convert": lambda x: x * 1e4,
            },  # J/cm**2 -> J/m**2
            "DR": {
                "name": "precipitation_duration",
                "convert": self.normalize_tenths,
            },  # 0.1 hour -> hour
            "RH": {
                "name": "precipitation",
                "convert": lambda x: x / 10 / 1000,
            },  # 0.1 mm -> m
            "RHX": {
                "name": "precipitation_max",
                "convert": lambda x: x / 10 / 1000,
            },  # 0.1 mm -> m
            "RHXH": {"name": "precipitation_max_hour", "convert": self.no_conversion},
            "PG": {
                "name": "air_pressure",
                "convert": lambda x: x / 10 * 100,
            },  # 0.1 hPa -> Pa
            "PX": {
                "name": "air_pressure_max",
                "convert": lambda x: x / 10 * 100,
            },  # 0.1 hPa -> Pa
            "PXH": {"name": "air_pressure_max_hour", "convert": self.no_conversion},
            "PN": {
                "name": "air_pressure_min",
                "convert": lambda x: x / 10 * 100,
            },  # 0.1 hPa -> Pa
            "PNH": {"name": "air_pressure_min_hour", "convert": self.no_conversion},
            "VVN": {"convert": self.knmi_visibility_class_to_meter_estimate},
            "VVNH": {"convert": self.knmi_visibility_class_to_meter_estimate},
            "VVX": {"convert": self.knmi_visibility_class_to_meter_estimate},
            "VVXH": {"convert": self.knmi_visibility_class_to_meter_estimate},
            "NG": {
                "name": "cloud_cover",
                "convert": self.no_conversion,
            },  # orig[1,2...0] -> orig[1,2...0]
            "UG": {"name": "humidity", "convert": self.percentage_to_frac},  # % -> frac
            "UX": {
                "name": "humidity_max",
                "convert": self.percentage_to_frac,
            },  # % -> frac
            "UXH": {"name": "humidity_max_hour", "convert": self.no_conversion},
            "UN": {
                "name": "humidity_min",
                "convert": self.percentage_to_frac,
            },  # % -> frac
            "UNH": {"name": "humidity_min_hour", "convert": self.no_conversion},
            "EV24": {"convert": lambda x: x / 10 / 1000},  # 0.1 mm -> m
        }

        self.to_human = copy.deepcopy(self.to_si)
        self.to_human["TG"]["convert"] = self.normalize_tenths  # 0.1 degree C -> C
        self.to_human["TN"]["convert"] = self.normalize_tenths  # 0.1 degree C -> C
        self.to_human["TX"]["convert"] = self.normalize_tenths  # 0.1 degree C -> C
        self.to_human["T10N"]["convert"] = self.normalize_tenths  # 0.1 degree C -> C
        self.to_human["RH"]["convert"] = self.normalize_tenths  # 0.1 mm -> mm
        self.to_human["RHX"]["convert"] = self.normalize_tenths  # 0.1 mm -> mm
        self.to_human["EV24"]["convert"] = self.normalize_tenths  # 0.1 mm -> mm

        self.human_to_model_specific = self._create_reverse_lookup(self.to_si)

        self.knmi_aliases = [
            "WIND",
            "TEMP",
            "SUNR",
            "PRCP",
            "PRES",
            "VICL",
            "MSTR",
            "ALL",
        ]

        logger.debug(f"Weather model [{self.id}] initialized successfully")

    def get_weather(
        self,
        coords: List[GeoPosition],
        begin: datetime,
        end: datetime,
        inseason=False,
        weather_factors: List[str] = None,
    ) -> xr.Dataset:
        """
            The function that gathers and processes the requested Daggegevens weather data from the KNMI site
            and returns it as a Xarray Dataset.
            (Though this model downloads from a specific download url, the question remains whether this source is also
            listed on the new KNMI Data Platform)
        Args:
            coords:             A list of GeoPositions containing the locations the data is requested for.
            begin:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            inseason:           A boolean representing the "inseason" parameter
            weather_factors:    A list of weather factors to request data for (in string format)
        Returns:
            An Xarray Dataset containing the weather data for the requested period, locations and factors.
        """
        # Test and account for invalid datetime timeframes or input
        begin, end = validate_begin_and_end(begin, end, None, datetime.utcnow() - relativedelta(days=1))
        # Get a list of the relevant STNs and choose the closest STN for each coordinate
        station_id, stns, _ = find_closest_stn_list(stations_history, coords)

        # Download the weather data for the relevant STNs
        raw_data = self._download_weather(
            stations=stns,
            start=begin,
            end=end,
            inseason=inseason,
            weather_factors=weather_factors,
        )

        # Parse the raw data into a Dataset
        raw_ds = self._parse_raw_weather_data(raw_data)

        # Prepare and format the weather data for output
        ds = self._prepare_weather_data(coords, station_id, raw_ds)

        # The KNMI model isn't working properly yet, so we have to cut out any overflow time-wise
        ds = ds.sel(time=slice(begin, end))
        return ds

    def is_async(self):  # pragma: no cover
        return self.async_model

    def _download_weather(
        self,
        stations: List[int],
        start: datetime,
        end: datetime,
        inseason=False,
        weather_factors: List[str] = None,
    ):
        """
            A function that downloads the weather from the KNMI download location and returns it as a text
        Args:
            stations:           A list containing the requested stations
            start:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            inseason:           A boolean representing the "inseason" parameter
            weather_factors:    A list of weather factors to request data for (in string format)
        Returns:
            A field containing the full response of the made download-request (text-based)
        """
        # fetch data
        params = self._create_request_params(start, end, inseason, stations, weather_factors)
        r = requests.post(url=self.download_url, data=params)

        if r.status_code != 200:
            raise requests.HTTPError(
                "Failed to retrieve data from the KNMI website",
                r.status_code,
                self.download_url,
                params,
            )
        return r.text

    def _create_request_params(self, start, end, inseason, stations, weather_factors):
        """
            A Function that transforms the request settings into parameters usable for the KMNI download request.
        Args:
            start:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            inseason:           A boolean representing the "inseason" parameter
            stations:           A list containing the requested stations
            weather_factors:    A list of weather factors to request data for (in string format)
        Returns:
            A params field (string) containing the matching settings for a KNMI Daggegevens download request.
        """
        params = {
            "fmt": "json",
            "stns": ":".join(str(station) for station in stations),
            "start": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
        }
        if inseason:
            params["inseason"] = "Y"

        if weather_factors is None:
            weather_factors = ["ALL"]

        updated_weather_factors = self._request_weather_factors(weather_factors)
        params["vars"] = ":".join(updated_weather_factors)

        return params

    def _parse_raw_weather_data(self, raw_data: str) -> xr.Dataset:
        json_data = json.loads(raw_data)
        dataframe_data = pd.DataFrame.from_dict(json_data, orient="columns")
        dataframe_data["date"] = pd.to_datetime(dataframe_data["date"])

        conversion_dict = {
            "station_code": int,
        }
        for weather_factor in self.to_si.keys():
            if weather_factor in dataframe_data.keys():
                conversion_dict[weather_factor] = np.float64

        dataframe_data = dataframe_data.astype(conversion_dict)
        dataframe_data = dataframe_data.set_index(["station_code", "date"])

        return dataframe_data.to_xarray()

    @staticmethod
    def _prepare_weather_data(coordinates: List[GeoPosition], station_id, raw_ds):
        # A function that prepares the weather data for return by the API, by replacing the matching station with the
        # lat/lon location that was requested, and properly formatting the dimensions.

        # re-arrange stns
        ds = raw_ds.sel(station_code=station_id)

        # dict of data
        data_dict = {var_name: (["coord", "time"], var.values) for var_name, var in ds.data_vars.items()}
        timeline = pd.DatetimeIndex(ds.coords["date"].values)

        ds = xr.Dataset(
            data_vars=data_dict,
            coords={"time": timeline, "coord": coords_to_pd_index(coordinates)},
        )
        ds = ds.unstack("coord")
        return ds

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
            elif f_low in self.human_to_model_specific:
                # KNMI daggegevens and uurgegevens with human names
                new_factors.append(self.human_to_model_specific[f_low])
            else:
                try:
                    if f_up in self.knmi_aliases:
                        new_factors.append(f_up)
                except AttributeError:
                    continue

        return list(set(new_factors))  # Cleanup any duplicate values and return
