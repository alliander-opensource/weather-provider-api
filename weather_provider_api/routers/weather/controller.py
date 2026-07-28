# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""Entry point to the weather provider."""

import datetime
import re

import numpy as np
import xarray as xr

from weather_provider_api.routers.weather.api_models import OutputUnit
from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.base_models.source import WeatherSourceBase
from weather_provider_api.routers.weather.exceptions import (
    UnknownModelException,
    UnknownSourceException,
)
from weather_provider_api.routers.weather.sources.cds.cds import CDS
from weather_provider_api.routers.weather.sources.knmi.knmi import KNMI
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class WeatherController:  # pragma: no cover
    """Controller for the Weather Provider API.

    This class is responsible for handling all requests for weather data, including fetching data from
    the appropriate sources and models, converting units, and formatting the output.
    """

    def __init__(self):
        """Load the available weather sources and their models into the controller."""
        source_instances: list[WeatherSourceBase] = [KNMI(), CDS()]
        self.sources: dict[str, WeatherSourceBase] = {source.id: source for source in source_instances}

    def get_weather(
        self,
        source_id: str,
        model_id: str,
        fetch_async: bool,
        coords: list[list[tuple[float, float]]],
        begin: datetime.datetime | None = None,
        end: datetime.datetime | None = None,
        factors: list[str] | None = None,
    ) -> xr.Dataset | None:
        """Get specific weather factors for a specific time and specific location(s).

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
        if not model:
            raise UnknownModelException(f"Model '{model_id}' not found for source '{source_id}'")

        # polygonal areas to mean calculation
        coordinate_list: list[tuple[float, float]] = self._calculate_polygon_means(coords)
        # conversion of Tuples with floats to GeoPosition items
        geo_positions: list[GeoPosition] = self._tuples_to_geo_positions(coordinate_list)

        if model.is_async():
            return None

        # call relevant routine data
        ds = model.get_weather(coords=geo_positions, begin=begin, end=end, weather_factors=factors)
        return ds

    def convert_names_and_units(
        self,
        source_id: str,
        model_id: str,
        fetch_async: bool,
        weather_data: xr.Dataset,
        unit: OutputUnit,
    ) -> xr.Dataset:
        """Convert the names and units of the weather data to match the requested output unit format."""
        model = self.get_model(source_id, model_id, fetch_async)
        if not model:
            raise UnknownModelException(f"Model '{model_id}' not found for source '{source_id}'")

        return model.convert_names_and_units(weather_data, unit)

    @staticmethod
    def lat_lon_to_coords(lat: float, lon: float) -> list[list[tuple[float, float]]]:
        """Convert a single pair of coordinates into a nested list format representing a single-point polygon."""
        return [[(lat, lon)]]

    @staticmethod
    def str_to_coords(locations_string: str) -> list[list[tuple[float, float]]]:
        """Convert a string containing coordinates into a list of tuples containing those coordinates."""
        str_coordinates_list = re.findall(r"\(\d{1,3}.?\d*,\s?\d{1,3}.?\d*\)", locations_string)
        coordinate_list: list[list[tuple[float, float]]] = []
        for str_coordinate in str_coordinates_list:
            no_spaces_str_coordinate: str = str_coordinate[1:-1].replace(" ", "")
            split_str_coordinate: list[str] = no_spaces_str_coordinate.split(",")
            coordinate: tuple[float, float] = (float(split_str_coordinate[0]), float(split_str_coordinate[1]))
            coordinate_list.append([coordinate])

        return coordinate_list

    def get_source_keys(self) -> list[str]:
        """Get a list of all available source keys."""
        return list(self.sources.keys())

    def get_sources(self) -> list[WeatherSourceBase]:
        """Get a list of all available sources."""
        return list(self.sources.values())

    def get_source(self, source_id: str) -> WeatherSourceBase | None:
        """Get a specific source by its ID."""
        self._validate_source(source_id)
        return self.sources.get(source_id, None)

    def get_models(self, source_id: str, fetch_async: bool = False) -> list[WeatherModelBase]:
        """Get a list of all available models for a specific source."""
        source = self.get_source(source_id)
        if source is None:
            return []
        return source.get_models(fetch_async)

    def get_model(self, source_id: str, model_id: str, fetch_async: bool = False) -> WeatherModelBase | None:
        """Get a specific model by its ID for a specific source."""
        self._validate_source_and_model(source_id, model_id, fetch_async)
        source = self.get_source(source_id)
        if source is None:
            return None
        return source.get_model(model_id, fetch_async)

    def _validate_source(self, source_id: str):
        """Validate that the provided source ID corresponds to a known source."""
        if source_id not in self.sources:
            raise UnknownSourceException

    def _validate_source_and_model(self, source_id: str, model_id: str, fetch_async: bool = False):
        """Validate that the provided source ID and model ID correspond to known entities."""
        self._validate_source(source_id)
        if self.sources[source_id].get_model(model_id, fetch_async) is None:
            raise UnknownModelException

    @staticmethod
    def _calculate_polygon_means(
        coords: list[list[tuple[float, float]]],
    ) -> list[tuple[float, float]]:
        """Calculate the mean latitude and longitude for each polygon in the provided list of coordinates.

        Given a 3-layer nested list:
            D0: different polygons
            D1: sequence of points in each polygon
            D2: coordinates of each point (lat, lon)
        Returns a list of (mean_lat, mean_lon) for each polygon.
        """
        means: list[tuple[float, float]] = []
        for polygon in coords:
            if not polygon:
                continue
            lats = [pt[0] for pt in polygon]
            lons = [pt[1] for pt in polygon]
            means.append((float(np.mean(lats)), float(np.mean(lons))))
        return means

    @staticmethod
    def _tuples_to_geo_positions(
        coords: list[tuple[float, float]],
    ) -> list[GeoPosition]:
        # Convert the Tuples in a list to a list of Geo Positions
        geo_positions = [GeoPosition(coordinate[0], coordinate[1]) for coordinate in coords]
        return geo_positions
