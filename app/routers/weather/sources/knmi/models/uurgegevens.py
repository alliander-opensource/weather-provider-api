#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""KNMI hour models data fetcher.
"""
import copy
from datetime import datetime
from io import StringIO
from typing import List, Optional

import numpy as np
import pandas as pd
import requests
import structlog
import xarray as xr
from dateutil.relativedelta import relativedelta

from app.routers.weather.base_models.model import WeatherModelBase
from app.routers.weather.sources.knmi.stations import stations_history
from app.routers.weather.sources.knmi.utils import find_closest_stn_list
from app.routers.weather.utils.date_helpers import validate_begin_and_end
from app.routers.weather.utils.geo_position import GeoPosition
from app.routers.weather.utils.pandas_helpers import coords_to_pd_index


class UurgegevensModel(WeatherModelBase):
    """
    A Weather Model that incorporates the:
        KNMI Uurgegevens
    dataset into the Weather Provider API
    """

    def __init__(self):
        super().__init__()
        self.id = "uurgegevens"
        self.name = "KNMI uurgegevens"
        self.version = None
        self.url = "https://projects.knmi.nl/klimatologie/uurgegevens/selectie.cgi"
        self.predictive = False
        self.time_step_size_minutes = 60
        self.num_time_steps = 0
        self.description = (
            "Hourly weather measurements. Can be returned for a specified period. "
            "The number of measurements returned depends on this period selection."
        )
        self.async_model = False

        self.to_si = {
            "DD": {"convert": self.no_conversion},
            "DDVEC": {
                "name": "wind_direction",
                "convert": self.no_conversion,
            },  # 360 N, 270 W ...
            "FH": {
                "name": "wind_speed",
                "convert": self.normalize_tenths,
            },  # 0.1 m/s -> m/s
            "FF": {"convert": self.normalize_tenths},  # 0.1 m/s -> m/s
            "FX": {
                "name": "wind_speed_max",
                "convert": self.normalize_tenths,
            },  # 0.1 m/s -> m/s
            "T": {
                "name": "temperature",
                "convert": self.tenth_celsius_to_kelvin,
            },  # 0.1 degree C -> Kelvin
            "T10N": {
                "name": "temperature_min_10cm",
                "convert": self.tenth_celsius_to_kelvin,
            },  # 0.1 degree C -> Kelvin
            "TD": {"convert": self.tenth_celsius_to_kelvin},  # 0.1 degree C -> Kelvin
            "SQ": {
                "name": "sunlight_duration",
                "convert": self.normalize_tenths,
            },  # 0.1 hour -> hour
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
            "P": {
                "name": "air_pressure",
                "convert": lambda x: x / 10 * 100,
            },  # 0.1 hPa -> Pa
            "VV": {
                "name": "visibility",
                "convert": self.knmi_visibility_class_to_meter_estimate,
            },
            "N": {
                "name": "cloud_cover",
                "convert": self.no_conversion,
            },  # orig[1,2...0] -> orig[1,2...0]
            "U": {
                "name": "humidity",
                "convert": self.percentage_to_frac,
            },  # % -> fraction
            "WW": {"convert": self.no_conversion},
            "IX": {"convert": self.no_conversion},
            "M": {"name": "fog_occurred", "convert": self.no_conversion},
            "R": {"name": "rain_occurred", "convert": self.no_conversion},
            "S": {"name": "snow_occurred", "convert": self.no_conversion},
            "O": {"name": "lightning_occurred", "convert": self.no_conversion},
            "Y": {"name": "icing_occurred", "convert": self.no_conversion},
        }

        self.to_human = copy.deepcopy(self.to_si)
        self.to_human["T"]["convert"] = self.normalize_tenths  # 0.1 degree C -> C
        self.to_human["T10N"]["convert"] = self.normalize_tenths  # 0.1 degree C -> C
        self.to_human["TD"]["convert"] = self.normalize_tenths  # 0.1 degree C -> C
        self.to_human["RH"]["convert"] = self.normalize_tenths  # 0.1 mm -> mm

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

        self.logger = structlog.get_logger(__name__)
        self.logger.debug(
            f"Weather model [{self.id}] initialized successfully",
            datetime=datetime.utcnow(),
        )

    def get_weather(
        self,
        coords: List[GeoPosition],
        begin: datetime,
        end: datetime,
        weather_factors: List[str] = None,
    ) -> xr.Dataset:
        """
            The function that gathers and processes the requested Uurgegevens weather data from the KNMI site
            and returns it as an Xarray Dataset.
            (Though this model downloads from a specific download url, the question remains whether this source is also
            listed on the new KNMI Data Platform)
        Args:
            coords:             A list of GeoPositions containing the locations the data is requested for.
            begin:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            weather_factors:    A list of weather factors to request data for (in string format)
        Returns:
            An Xarray Dataset containing the weather data for the requested period, locations and factors.

        NOTES:
            Besides the singular weather factors, Uurgegevens also knows the following weather factor groups:
            WIND == DD:FH:FF:FX       -Wind
            TEMP == T:T10N:TD         -Temperature
            SUNR == SQ:Q              -Sunshine duration and global radiation
            PRCP == DR:RH             -Precipitation and potential evaporation
            VICL == VV:N:U            -Visibility, cloud cover and relative humidity
            WEER == M:R:S:O:Y:WW      -Weather phenomena, weather types
            ALL  == All of the factors
        """
        # TODO: Switch to KNMI Data Platform when supported (and found)

        # Get a list of relevant STNs to a location, and choose the closest STN
        coords_stn, stns, coords_stn_ind = find_closest_stn_list(
            stations_history, coords
        )

        updated_weather_factors = self._request_weather_factors(weather_factors)

        # download weather data
        raw_data = self._download_weather(stns, begin, end, updated_weather_factors)

        # parse raw data
        raw_ds = self._parse_raw_data(raw_data)

        # prepare the weather data for output
        ds = self._prepare_weather_data(coords, coords_stn, raw_ds)

        ds = ds.sel(time=slice(begin, end))
        return ds

    def is_async(self):  # pragma: no cover
        return self.async_model

    def _download_weather(
        self,
        stations: List[int],
        begin: datetime,
        end: datetime,
        weather_factors: List[str] = None,
    ):
        """
            A function that downloads the weather from the KNMI download location and returns it as a text
        Args:
            stations:           A list containing the requested stations
            begin:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            weather_factors:    A list of weather factors to request data for (in string format)
        Returns:
            A field containing the full response of the made download-request (text-based)
        """
        url = "http://projects.knmi.nl/klimatologie/uurgegevens/getdata_uur.cgi"

        # Validate begin and end datetimes
        begin, end = validate_begin_and_end(
            begin, end, None, datetime.utcnow() - relativedelta(days=1)
        )

        # fetch data
        params = self._create_request_params(begin, end, stations, weather_factors)
        r = requests.post(url=url, data=params)
        if r.status_code != 200:
            raise requests.HTTPError(
                "The KNMI website is down!", r.status_code, url, params
            )
        return r.text

    @staticmethod
    def _create_request_params(begin, end, stations, weather_factors):
        """
            A Function that transforms the request settings into parameters usable for the KMNI download request.
        Args:
            begin:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            stations:           A list containing the requested stations
            weather_factors:    A list of weather factors to request data for (in string format)
        Returns:
            A params field (string) containing the matching settings for a KNMI Daggegevens download request.
        """

        # Build the parameter dictionary for the download request.
        params = {
            "stns": ":".join(str(station) for station in stations),
            "start": f"{begin.strftime('%Y%m%d')}01",
            "end": f"{end.strftime('%Y%m%d')}24",
        }

        if weather_factors is None:
            weather_factors = ["ALL"]

        params["vars"] = ":".join(weather_factors)
        return params

    @staticmethod
    def _parse_raw_data(raw_data: str) -> xr.Dataset:
        """
            A function that parses the raw data (string-based) from the KNMI Daggegevens dataset into an Xarray Dataset
        Args:
            raw_data:   The raw text from the file as it was downloaded from the download link.
        Returns:
            An Xarray Dataset that holds all of the weather data that was in the original raw_data, but formatted.
        """
        raw_data = raw_data.replace("# STN,YYYYMMDD", "STN,YYYYMMDD")  # Clean up

        # First convert to a Pandas Dataframe
        cols = (
            pd.read_csv(
                StringIO(raw_data),
                comment="#",
                nrows=1,
                header=None,
                skipinitialspace=True,
            )
            .T.drop_duplicates()
            .index
        )

        df = pd.read_csv(
            StringIO(raw_data),
            comment="#",
            header=0,
            skipinitialspace=True,
            usecols=cols,
        )

        # Then parse the Dataframe
        df["int_date_time"] = df["YYYYMMDD"] * 100 + df["HH"] - 1
        df["time"] = pd.to_datetime(df["int_date_time"], format="%Y%m%d%H")
        del df["YYYYMMDD"]
        del df["int_date_time"]
        del df["HH"]
        df.set_index(["time", "STN"], inplace=True)
        df = df.astype(np.float64)

        # Finally, convert into a Xarray Dataset
        ds = df.to_xarray()
        return ds

    @staticmethod
    def _prepare_weather_data(coordinates, coords_stn, raw_ds):
        # A function that prepares the weather data for return by the API, by replacing the matching station with the
        # lat/lon location that was requested, and properly formatting the dimensions.

        # re-arrange stns
        ds = raw_ds.sel(STN=coords_stn)
        # dict of data
        data_dict = {
            var_name: (["time", "coord"], var.values)
            for var_name, var in ds.data_vars.items()
        }
        timeline = ds.coords["time"].values
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

        return list(set(new_factors))  # Cleanup any duplicate values and return
