#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" KNMI current weather data fetcher.
"""
import copy
import locale
import re
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
import requests
import structlog
import xarray as xr

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.sources.knmi.stations import (
    stations_actual,
    stations_actual_reversed,
)
from weather_provider_api.routers.weather.sources.knmi.utils import (
    find_closest_stn_list,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.pandas_helpers import coords_to_pd_index

logger = structlog.get_logger(__name__)


class ActueleWaarnemingenModel(WeatherModelBase):
    """
    A Weather Model that incorporates the:
    "KNMI Actuele Waarnemingen" dataset into the Weather Provider API
    """

    def __init__(self):
        super().__init__()
        self.id = "waarnemingen"
        self.name = "KNMI Actuele Waarnemingen"
        self.version = None
        self.url = "https://www.knmi.nl/nederland-nu/weer/waarnemingen"
        self.predictive = False
        self.time_step_size_minutes = 10
        self.num_time_steps = 1
        self.description = "Current weather observations. Updated every 10 minutes."
        self.async_model = False

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
        The function that gathers and processes the requested Actuele Waarnemingen weather data from the KNMI site
        and returns it as a Xarray Dataset.
        (This model interprets directly from an HTML page, but the information is also available from the data
        platform. Due to it being rather impractically handled, we stick to the site for now.)

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

        # Download the current weather data
        raw_ds = self._download_weather()

        # Get a list of the relevant STNs and choose the closest STN for each coordinate
        coords_stn, stns, coords_stn_ind = find_closest_stn_list(
            stations_actual, coords
        )

        # Select the data for the found closest STNs
        ds = raw_ds.sel(STN=coords_stn)

        data_dict = {
            var_name: (["time", "coord"], var.values)
            for var_name, var in ds.data_vars.items()
            if var_name in updated_weather_factors and var_name not in ["lat", "lon"]
        }

        timeline = ds.coords["time"].values

        ds = xr.Dataset(
            data_vars=data_dict,
            coords={"time": timeline, "coord": coords_to_pd_index(coords)},
        )
        ds = ds.unstack("coord")
        return ds

    def _download_weather(self) -> Optional[xr.Dataset]:
        """
        A function that downloads the Actuele Waarnemingen site and parses it into a Weather Provider API compatible
        format.

        Returns:
            An Xarray Dataset containing the parsed weather data.
        """
        raw_ds = None

        try:
            knmi_site_response = requests.get(self.url)

            if knmi_site_response.ok:
                knmi_site_df = pd.read_html(knmi_site_response.text)[0]

                column_translations = {
                    "Station": "station",
                    "Weer": "weather_description",
                    "Temp (°C)": "temperature",
                    "Chill (°C)": "wind_chill",
                    "RV (%)": "relative_humidity",
                    "Wind (bft)": "wind_direction",
                    "Wind (m/s)": "wind_speed",
                    "Wind (km/uur)": "wind_speed_kmu",
                    "Zicht (m)": "visibility",
                    "Druk (hPa)": "air_pressure",
                }

                # Rename to the conventional naming system used for the Weather Provider API
                for dictionary_item in knmi_site_df.columns.copy(deep=True):
                    if dictionary_item in column_translations.keys():
                        knmi_site_df = knmi_site_df.rename(
                            columns={
                                dictionary_item: column_translations[dictionary_item]
                            }
                        )
                    else:
                        knmi_site_df = knmi_site_df.drop(
                            dictionary_item, axis="columns"
                        )

                current_observation_moment = self.retrieve_observation_moment(
                    knmi_site_response.text
                )
                knmi_site_df["time"] = current_observation_moment
                if "wind_direction" in knmi_site_df:
                    knmi_site_df["wind_direction"] = knmi_site_df[
                        "wind_direction"
                    ].str.strip("\n")

                # Add a field for the station with its (lat, lon)-coordinates and remove the original station code
                knmi_site_df["STN"] = knmi_site_df["station"].apply(
                    lambda x: stations_actual_reversed[x.upper()]
                )

                stations_actual_indexed = stations_actual.set_index("STN")

                knmi_site_df["lat"] = knmi_site_df["STN"].apply(
                    lambda x: stations_actual_indexed.loc[x, "lat"]
                )
                knmi_site_df["lon"] = knmi_site_df["STN"].apply(
                    lambda x: stations_actual_indexed.loc[x, "lon"]
                )
                knmi_site_df = knmi_site_df.drop("station", axis="columns")

                # Rebuild the index
                knmi_site_df = knmi_site_df.set_index(["time", "STN"])

                # The following fields get removed because they aren't currently used in this API
                if "weather_description" in knmi_site_df:
                    knmi_site_df = knmi_site_df.drop(
                        "weather_description", axis="columns"
                    )
                if "wind_chill" in knmi_site_df:
                    knmi_site_df = knmi_site_df.drop("wind_chill", axis="columns")

                # Generate a Xarray DataSet
                raw_ds = knmi_site_df.to_xarray()

        except (requests.exceptions.BaseHTTPError, IndexError) as e:
            logger.exception(str(e))

        return raw_ds

    @staticmethod
    def retrieve_observation_moment(html_body: str):
        """
        A function that extracts the observation date from the supplied html body of the Actuele Waarnemingen site.

        Args:
            html_body:  The text from the body downloaded from the Actuele Waarnemingen Site.

        Returns:
            Either the matching datetime if it can be extracted, or the current datetime if it cannot.
        """
        try:
            re_match = re.search(
                r"Waarnemingen\s(\d+\s\w+\s\d{4}\s\d{2}:\d{2})\suur",
                html_body,
            )
            if re_match:
                dt_str = re_match.group(1)
                current_locale = locale.getlocale(locale.LC_TIME)
                locale.setlocale(locale.LC_TIME, "dutch")
                dt = datetime.strptime(dt_str, "%d %B %Y %H:%M")
                locale.setlocale(locale.LC_TIME, current_locale)
                return dt
        except Exception as e:
            logger.exception(
                "An exception occurred while retrieving the KNMI Waarnemingen timestamp. Using current datetime.",
                error=e,
            )
            return datetime.now()

        current_locale = locale.getlocale(locale.LC_TIME)
        locale.setlocale(locale.LC_TIME, "dutch")
        dt = datetime.now()
        locale.setlocale(locale.LC_TIME, current_locale)
        return dt

    def is_async(self):  # pragma: no cover
        return self.async_model

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
