#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""Entry point to the weather provider."""
import datetime
import re
from typing import List, Optional, Tuple

import numpy as np
import xarray as xr

from weather_provider_api.routers.weather.api_models import OutputUnit
from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.base_models.source import WeatherSourceBase
from weather_provider_api.routers.weather.exceptions import UnknownModelException, UnknownSourceException
from weather_provider_api.routers.weather.sources.cds.cds import CDS
from weather_provider_api.routers.weather.sources.knmi.knmi import KNMI
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class WeatherController(object):  # pragma: no cover
    """
    A Controller Object that can handle any request for the hooked up weather models and format it into any of the
    hooked up output formats.
    """

    def __init__(self):
        # Load Sources (and with it their models) and hook them up to the controller
        source_instances = [KNMI(), CDS()]
        self.sources = {source.id: source for source in source_instances}

    def get_weather(
        self,
        source_id: str,
        model_id: str,
        fetch_async: bool,
        coords: List[List[Tuple[float, float]]],
        begin: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
        factors: List[str] = None,
    ):
        """
            Function to use the requested weather model from the requested source to get specific weather factors for a
            specific time and specific location(s)
        Args:
            source_id:  The weather source that need to be queried (e.g.: knmi, cds)
            model_id:   The model identifier of the model that needs to be queried (has to be a model that exists within
                        the specific source requested through source_id
            fetch_async:    A boolean indicated if the request was made to asynchronously fetch the data or not
            coords:     A nested 3-layer list representing a list of polygons
                        in the case of points, they are treated as a one-point polygon
                        D0: different polygons
                        D1: sequence of points in each polygon
                        D2: coordinates of each point (lat, lon in coordinates)
            begin:      The starting time of the requested output data
            end:        The ending time of the requested output data
            factors:    A list of the requested weather factors for the output (default is all available)

        Returns:
            A Xarray Dataset containing the weather data for the selected model, period(s), location(s) and factor(s)
        """
        model = self.get_model(source_id, model_id, fetch_async)
        coords = self._calculate_polygon_means(coords)  # polygonal areas to mean calculation
        coords = self._tuples_to_geo_positions(coords)  # conversion of Tuples with floats to GeoPosition items

        if model.is_async():
            return None

        # call relevant routine data
        ds = model.get_weather(coords=coords, begin=begin, end=end, weather_factors=factors)
        return ds

    def convert_names_and_units(
        self,
        source_id: str,
        model_id: str,
        fetch_async: bool,
        weather_data: xr.Dataset,
        unit: OutputUnit,
    ):
        # A function that uses the indicated model's built-in conversion method to alter the values in a given dataset
        # to match the requested output unit format.
        model = self.get_model(source_id, model_id, fetch_async)
        ds = model.convert_names_and_units(weather_data, unit)
        return ds

    @staticmethod
    def lat_lon_to_coords(lat: float, lon: float) -> List[List[Tuple[float, float]]]:
        return [[(lat, lon)]]

    @staticmethod
    def str_to_coords(locations_string: str):
        str_coordinates_list = re.findall(r"\(\d{1,3}.?\d*,\s?\d{1,3}.?\d*\)", locations_string)
        coordinate_list = []
        for str_coordinate in str_coordinates_list:
            coordinate = str_coordinate[1:-1].replace(" ", "")
            coordinate = coordinate.split(",")
            coordinate = (float(coordinate[0]), float(coordinate[1]))
            coordinate_list.append([coordinate])

        return coordinate_list

    def get_source_keys(self) -> List[str]:
        return list(self.sources.keys())

    def get_sources(self) -> List[WeatherSourceBase]:
        return list(self.sources.values())

    def get_source(self, source_id: str) -> Optional[WeatherSourceBase]:
        self._validate_source(source_id)
        return self.sources.get(source_id, None)

    def get_models(self, source_id: str, fetch_async: bool = False) -> List[WeatherModelBase]:
        source = self.get_source(source_id)
        return source.get_models(fetch_async)

    def get_model(self, source_id: str, model_id: str, fetch_async: bool = False) -> Optional[WeatherModelBase]:
        self._validate_source_and_model(source_id, model_id, fetch_async)
        source = self.get_source(source_id)
        return source.get_model(model_id, fetch_async)

    def _validate_source(self, source_id: str):
        if source_id not in self.sources:
            raise UnknownSourceException

    def _validate_source_and_model(self, source_id: str, model_id: str, fetch_async: bool = False):
        self._validate_source(source_id)
        if self.sources[source_id].get_model(model_id, fetch_async) is None:
            raise UnknownModelException

    @staticmethod
    def _calculate_polygon_means(coords: List[List[Tuple[float, float]]]) -> List[Tuple[float, float]]:
        # Calculating the mean points of polygons containing locations
        coords = [
            (
                float(np.mean([single_point[0] for single_point in single_polygon])),
                float(np.mean([single_point[1] for single_point in single_polygon])),
            )
            for single_polygon in coords
        ]
        return coords

    @staticmethod
    def _tuples_to_geo_positions(coords: List[Tuple[float, float]]) -> List[GeoPosition]:
        # Convert the Tuples in a list to a list of Geo Positions
        coords = [GeoPosition(coordinate[0], coordinate[1]) for coordinate in coords]
        return coords
