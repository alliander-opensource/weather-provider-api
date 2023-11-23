#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""Utilities for handling KNMI datasets.
"""
import locale
import re
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd
import requests
import xarray as xr
from geopy.distance import great_circle
from loguru import logger

from weather_provider_api.routers.weather.sources.knmi.stations import (
    stations_actual,
    stations_actual_reversed,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


def find_closest_stn_list(stn_stations: pd.DataFrame, coords: List[GeoPosition]):
    """
            A function that finds the closest stations to the locations in the given list of GeoPositions
    Args:
            stn_stations:   A Pandas Dataframe containing all the station data for the KNMI stations
            coords:         A list of GeoPositions with locations to find the nearest stations to.
        Returns:
            A list of coordinates for found stations
            A list of found stations in the same order
            A list of index numbers for the found in the same order
    """
    _stn_stations = stn_stations.copy(deep=True)

    # get list of relevant STNs, choose closest STN
    coords_stn = [_find_closest_stn_single(_stn_stations, coord) for coord in coords]
    stns = list(set(coords_stn))
    coords_stn_ind = [stns.index(x) for x in coords_stn]
    return coords_stn, stns, coords_stn_ind


def _find_closest_stn_single(stn_stations: pd.DataFrame, coord: GeoPosition):
    """
        A function that finds the closest station to a single GeoPosition
    Args:
        stn_stations:   A Pandas Dataframe containing all the station data for the KNMI stations
        coord:          A GeoPosition to find the nearest station for
    Returns:
        A station number indicating its index in the supplied dataframe.
    """
    stn_stations["distance"] = stn_stations.apply(
        lambda x: great_circle((x["lat"], x["lon"]), coord.get_WGS84()).km, axis=1
    )

    # Find the stn with the lowest distance to the location
    min_ind = np.argmin(stn_stations["distance"].values)
    # Return the found stn
    return stn_stations.loc[min_ind, "STN"]


def download_actuele_waarnemingen_weather() -> xr.Dataset:
    """ """
    raw_ds = None

    try:
        knmi_site_response = requests.get("https://www.knmi.nl/nederland-nu/weer/waarnemingen")

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
                    knmi_site_df = knmi_site_df.rename(columns={dictionary_item: column_translations[dictionary_item]})
                else:
                    knmi_site_df = knmi_site_df.drop(dictionary_item, axis="columns")

            current_observation_moment = _retrieve_observation_moment(knmi_site_response.text)
            knmi_site_df["time"] = current_observation_moment
            knmi_site_df["time"] = knmi_site_df["time"].astype("datetime64[ns]")
            if "wind_direction" in knmi_site_df:
                knmi_site_df["wind_direction"] = knmi_site_df["wind_direction"].str.strip("\n")

            # Add a field for the station with its (lat, lon)-coordinates and remove the original station code
            knmi_site_df["STN"] = knmi_site_df["station"].apply(lambda x: stations_actual_reversed[x.upper()])

            stations_actual_indexed = stations_actual.set_index("STN")

            knmi_site_df["lat"] = knmi_site_df["STN"].apply(lambda x: stations_actual_indexed.loc[x, "lat"])
            knmi_site_df["lon"] = knmi_site_df["STN"].apply(lambda x: stations_actual_indexed.loc[x, "lon"])
            knmi_site_df = knmi_site_df.drop("station", axis="columns")

            # Rebuild the index
            knmi_site_df = knmi_site_df.set_index(["time", "STN"])

            # The following fields get removed because they aren't currently used in this API
            if "weather_description" in knmi_site_df:
                knmi_site_df = knmi_site_df.drop("weather_description", axis="columns")
            if "wind_chill" in knmi_site_df:
                knmi_site_df = knmi_site_df.drop("wind_chill", axis="columns")

            # Generate a Xarray DataSet
            raw_ds = knmi_site_df.to_xarray()

    except (requests.exceptions.BaseHTTPError, IndexError) as expected_error:
        logger.exception(str(expected_error))

    return raw_ds


def _retrieve_observation_moment(html_body: str) -> datetime:
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
    except locale.Error:
        logger.warning(
            "No locale could be determined for KNMI Waarnemingen datetime transformation. "
            "Using local datetime instead."
        )
        return datetime.now()
    except Exception as e:
        logger.exception(
            "An unknown exception occurred while retrieving the KNMI Waarnemingen datetime for use in the response."
            f" Using local datetime instead. Error: {e}"
        )
        return datetime.now()

    current_locale = locale.getlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, "dutch")
    dt = datetime.now()
    locale.setlocale(locale.LC_TIME, current_locale)
    return dt
