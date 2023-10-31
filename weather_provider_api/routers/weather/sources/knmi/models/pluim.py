#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""KNMI day part prediction data fetcher.
"""
import copy
from datetime import datetime
from typing import List, Optional

import numpy as np
import requests
import xarray as xr
from dateutil.relativedelta import relativedelta
from loguru import logger

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.sources.knmi.stations import stations_prediction
from weather_provider_api.routers.weather.sources.knmi.utils import find_closest_stn_list
from weather_provider_api.routers.weather.utils.date_helpers import validate_begin_and_end
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.pandas_helpers import coords_to_pd_index


class PluimModel(WeatherModelBase):
    """
    A Weather Model that incorporates the:
        KNMI Pluim
    dataset into the Weather Provider API
    """

    def __init__(self):
        super().__init__()
        self.id = "pluim"
        logger.debug(f"Initializing weather model [{self.id}]")

        self.name = "ECMWF pluim"
        self.version = ""
        self.url = "https://www.knmi.nl/nederland-nu/weer/waarschuwingen-en-verwachtingen/weer-en-klimaatpluim"
        self.predictive = True
        self.time_step_size_minutes = 720
        self.num_time_steps = 30
        self.description = (
            "Predictions for the coming 15 days, current included, with two predictions made for each day."
        )
        self.async_model = False

        self.to_si = {
            "wind_speed": {
                "name": "wind_speed",
                "convert": self.kmh_to_ms,  # km/h -> m/s
                "code": 11012,
            },
            "wind_direction": {
                "name": "wind_direction",
                "convert": self.no_conversion,  # 360N, 270W, ...
                "code": 11011,
            },
            "short_time_wind_speed": {
                "name": "wind_speed_max",
                "convert": self.kmh_to_ms,  # km/h -> m/s
                "code": 11041,
            },
            "temperature": {
                "name": "temperature",
                "convert": self.celsius_to_kelvin,  # degree C -> Kelvin
                "code": 99999,
            },
            "precipitation": {
                "name": "precipitation",
                "convert": lambda x: x / 1000,  # mm -> m
                "code": 13021,
            },
            "precipitation_sum": {
                "name": "precipitation_sum",
                "convert": lambda x: x / 1000,  # mm -> m
                "code": 13011,
            },
            "cape": {
                "name": "cape",
                "convert": lambda x: x / 1000,
                "code": 13241,
            },  # J/kg
        }

        self.to_human = copy.deepcopy(self.to_si)
        self.to_human["temperature"]["convert"] = self.no_conversion  # C -> C
        self.to_human["precipitation"]["convert"] = self.no_conversion  # mm
        self.to_human["precipitation_sum"]["convert"] = self.no_conversion  # mm

        self.human_to_model_specific = self._create_reverse_lookup(self.to_si)

        logger.debug(f"Weather model [{self.id}] initialized successfully")

    def get_weather(
        self,
        coords: List[GeoPosition],
        begin: datetime,
        end: datetime,
        weather_factors: List[str] = None,
        **_kwargs,
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
            weather_factors:    A list of weather factors to request data for (in string format)
        Returns:
            An Xarray Dataset containing the weather data for the requested period, locations and factors.
        """

        # Test and account for invalid datetime timeframes or input
        begin, end = validate_begin_and_end(begin, end, datetime.utcnow(), datetime.utcnow() + relativedelta(days=15))

        # get list of relevant STNs, choose closest STN
        _, stns, coords_stn_ind = find_closest_stn_list(stations_prediction, coords)

        # load default weather factors if unspecified
        if weather_factors is None:
            weather_factors = self.to_si.keys()

        # download the weather factors for all stations
        ds = self._download_weather(coords, coords_stn_ind, stns, weather_factors)

        ds = self._select_weather_from_given_period(ds, begin, end)
        ds = ds.dropna("time", "all")  # Dropping any times that only carry NaN values

        return ds

    @staticmethod
    def _select_weather_from_given_period(ds: xr.Dataset, begin: datetime, end: datetime):
        """
            A function that filters the given Xarray Dataset to only the requested period.
        Args:
            ds:     An Xarray Dataset to be filtered
            begin:  A datetime containing the start of the period to filter.
            end:    A datetime containing the end of the period to filter.
        Returns:
            An Xarray Dataset containing all the data from the original dataset that matches the given period.
        """
        begin, end = validate_begin_and_end(
            begin,
            end,
            datetime.today().replace(hour=0, minute=0, second=0),
            datetime.today().replace(hour=0, minute=0, second=0) + relativedelta(days=15),
        )
        ds = ds.sel(time=slice(begin, end))
        return ds

    def is_async(self):  # pragma: no cover
        return self.async_model

    def _download_weather(
        self,
        coordinates: List[GeoPosition],
        coords_stn_ind,
        stns,
        weather_factors: List[str],
    ):
        """
            A function that downloads the requested weather data, factor by factor.
        Args:
            coordinates:        A list of GeoPositions containing the coordinates to request data for.
            coords_stn_ind:     A list of station coordinates in order
            stns:               A list of stations by ID in the same order
            weather_factors:    A list of weather factors to request the data for (string based)
        Returns:
            An Xarray Dataset containing the requested factors for the requested period and location(s).
        """
        arr_dict = {}
        ds = xr.Dataset()
        for weather_factor in weather_factors:
            try:
                # Convert the factor to its request code
                code = self.to_si[weather_factor]["code"]
            except KeyError:
                # Requested factor is unknown: skip
                continue

            # Download the requested factor
            timeline, value = self._download_single_factor(stns, code)

            # add values
            arr_dict[weather_factor] = xr.DataArray(
                data=value[:, coords_stn_ind],
                dims=["time", "coord"],
                coords={"time": timeline, "coord": coords_to_pd_index(coordinates)},
                name=weather_factor,
            )
            ds = xr.merge(arr_dict.values(), join="outer")
        ds = ds.unstack("coord")
        return ds

    @staticmethod
    def _download_single_stn_factor(stn: int, factor: int):
        """
            A function to download a single factor for a single station
        Args:
            stn:    The station (ID) to download the factor for
            factor: The weather factor to download
        Returns:
            A list of datetime64 items holding the times for the factors, and a matching list of values holding
            values belonging to the requested factor during those times.
        """
        base_url = (
            f"https://cdn.knmi.nl/knmi/json/page/weer/waarschuwingen_verwachtingen/ensemble/iPluim/{stn}_{factor}.json"
        )

        response = requests.get(base_url)
        if response.status_code != 200:
            raise requests.HTTPError(
                "Failed to retrieve data from the KNMI website",
                response.status_code,
                base_url,
            )

        series = response.json()["series"]
        # only retrieve prediction
        prediction_data = [x for x in series if "Verwacht" in x["name"]][0]["data"]
        if isinstance(prediction_data[0], dict):
            # get timeline
            timeline = np.array([x["x"] for x in prediction_data]).astype("datetime64[ms]")
            # get value
            value = np.array([x["y"] for x in prediction_data], dtype=np.float64)
        else:
            # get timeline
            timeline = np.array([x[0] for x in prediction_data]).astype("datetime64[ms]")
            # get value
            value = np.array([x[1] for x in prediction_data], dtype=np.float64)

        return timeline, value

    def _download_single_factor(self, stns: list, factor: int):
        """
            A function that downloads a single factor for all the given stations
        Args:
            stns:   A list of stations to download the factor for.
            factor: The weather factor to download.
        Returns:
            A list holding a timeline in datetime64 items as returned from the download requests, matching the request,
            and a list holding the values for the requested factor for all the stations in the order:
                Station, Timeline
        """
        values = []
        timeline = []
        for stn in stns:
            timeline, value = self._download_single_stn_factor(stn, factor)
            values.append(value)
        return timeline, np.stack(values, axis=1)

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
