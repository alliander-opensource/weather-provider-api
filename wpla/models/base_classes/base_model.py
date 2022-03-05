#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from abc import abstractmethod
from datetime import datetime
from typing import List, Tuple, Optional

import numpy as np
import structlog
import xarray as xr

from wpla.models.base_classes.abc_enhanced import ABCEnhanced
from wpla.models.generic_utils.geo_positioning import GeoCoordinateSystem
from wpla.models.generic_utils.unit_system_conversion import UnitSystem


class WeatherModelBase(metaclass=ABCEnhanced):
    required_attributes = [
        'short_name',  # The short name and ID of the WeatherModel
        'long_name',  # A longer more descriptive name for the WeatherModel
        'content_description',  # A short description of what the model at any given moment should contain and what
        # the WeatherModel implements of those contents (if not everything)
        'usage_licenses',  # One or more license types that apply to the meteorological data the WeatherModel gathers
        'latest_version',  # The latest known supported version of the gathered data
        # Should use the version the data als uses if possible, otherwise should use the
        # last known date the model works as a reference value
        'information_url',  # A URL indicating where to find more information on the model and the data it contains
        'data_grid',  # Information on grid type the data uses (like WGS84) and on what resolution it does so
        'update_frequency',  # How often source data for the model gets refreshed
        'request_timeframe'  # The full time range from which data can be requested from the model
        # (using the WeatherModel). To be used when validating the timeframe for requests.
        # Suggested format is a Tuple of datetimes.
    ]

    TIME_STRING_FORMAT = "%Y-%m-%d %H:%m"  # Base format of time used for timeframe validation

    def __init__(self):
        self.logger = structlog.getLogger(__name__)

        # Can the model by synchronously called?
        # Default value is False, to be overwritten if true from the model itself
        self.synchronous = False

        # Is the model predictive in nature?
        # Default value is False, to be overwritten if true from the model itself
        self.predictive = False

        # What type of repository should be used?
        # The Default value is None, to be overwritten if a repository is required
        self.repository_type = None

    @abstractmethod
    def get_weather(
            self,
            coordinates: List[Tuple[np.float64, np.float64]],
            timeframe: Tuple[Optional[datetime], Optional[datetime]],
            weather_factors: List[str] = None,
            extrapolate_weather: bool = False,
            swap_coordinates: bool = False,
            coord_system: GeoCoordinateSystem = GeoCoordinateSystem.WGS84,
    ) -> xr.Dataset:
        """The main method for retrieving harmonized weather data from a WeatherModel as a Xarray Dataset.

        Args:
            coordinates: A list of Tuples holding coordinates to use. The default format is WGS84.
            timeframe: A tuple holding the timeframe for which to gather data in the format (start, end)
                       Default values will be assumed for either value if missing, based on the WeatherModel's own
                       assumptions. Usually about a reasonable amount of data near to the current date will be returned.
            weather_factors: A list of strings indicating the weather factors to be gathered. These can consist of
                             harmonized names, the base model's own names or a mix thereof. If no list is supplied a
                             default set of data will be gathered. If a list containing invalid factors is requested,
                             an InvalidWeatherRequestException will be raised accordingly
            extrapolate_weather: A boolean holding whether to extrapolate weather to the requested coordinates (True)
                                 or just find the nearest point available (False). Extrapolation methods may vary per
                                 WeatherSource or WeatherModel, and some WeatherModels may not even have extrapolation
                                 available. In those cases, the nearest point should always be returned.
            swap_coordinates: A boolean holding whether to return the gathered data with the coordinates swapped with
                              those of the found data (True), or with those coordinates added as extra fields.
                              This only applies if the weather is not being extrapolated to the requested coordinates.
            coord_system: A descriptor indicating which GeoCoordinateSystem the supplied coordinates are in.
                          The default is GeoCoordinateSystem.WGS84, or 'wgs84'.

        Returns:
            A Xarray Dataset holding the requested weather data, fully harmonized

        Note:
            The returned harmonized weather dataset should also contain a metadata "short_name" value holding the
            WeatherModel's short_name (id) for validation when using transformations into other unit systems or
            retrieving the original factor names.
        """
        raise NotImplementedError

    def validate_coordinates(
            self,
            coordinates: List[Tuple[np.float64, np.float64]],
            coord_system: GeoCoordinateSystem = GeoCoordinateSystem.WGS84
    ) -> List[Tuple[np.float64, np.float64]]:
        """This function should validate all coordinates in a list to the WeatherModel's allowed grid. Depending on the
        model in question this could be anything from verifying its placement inside a fully detailed map of a
        continent, country or region, to a bounding box holding any size of area.

        Args:
            coordinates: A List of Tuples holding coordinates to validate.
            coord_system: The GeoCoordinateSystem the coordinates are currently formatted in.
                          Used to transform the coordinates back to their original format after validation if needed.
                          This also allows for "pre-validation" of a set of coordinates with a WeatherModel.

        Returns:
            A list of validated coordinates. Non-valid coordinates have been removed and should add debug-information
            on this to the logs. If no valid coordinates remain an InvalidWeatherRequestException will be raised.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_timeframe(
            self,
            timeframe: Tuple[Optional[datetime], Optional[datetime]]
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """The purpose of this function is to validate the timeframe for any given request. If it makes sense for the
        WeatherModel in question any missing or invalid values should be replaced by default values, otherwise an
        InvalidWeatherRequestException should be raised.

        Args:
            timeframe: A Tuple of two values holding up to two datetimes.

        Returns:
            A tuple of two datetime values. Either a valid timeframe should be returned or an Exception raised.

        """
        raise NotImplementedError

    @abstractmethod
    def transform_dataset(
            self,
            source_dataset: xr.Dataset,
            unit_system: UnitSystem = UnitSystem.SI,
            use_harmonized_names: bool = True,
            validity_overwrite: bool = False
    ) -> xr.Dataset:
        """This is the main function used for re-formatting any harmonized data into the requested unit system or
        retrieving the source model's original names for its factors.

        Args:
            source_dataset: A Xarray Dataset holding the weather data to reformat.
            unit_system: The UnitSystem (enum class) value that indicates the intended target system to convert to.
            use_harmonized_names: A boolean holding whether to use the harmonized names (True) or the ones used by the
                                  original source data. The default is True (harmonized names)
            validity_overwrite: A boolean holding whether to check validity of a source_dataset by reading the
                                "short_name" metadata property (False), or to just assume dataset formatting is
                                valid (True)

        Returns:
            A Xarray Dataset with the same data as the source_dataset, but now altered to use the requested UnitSystem
            and naming convention.

        Note:
            The source_dataset object should contain a metadata "short_name" value to identify it as a valid dataset
            for the function.

        Note:
            If the source_dataset is formatted in any other unit system than SI, it should also hold a metadata
            "unit_system" value, containing which unit system that is.

        Note:
            A WeatherModel class is free to allow for the transformation of not properly formatted or validated
            datasets, but should always properly work with the metadata therein. At the very least the data
            transformation should implement transformation between the original data and the 'SI' unit system format,
            but the standard is definitely 'all of the official UnitSystem types'!

        """
        raise NotImplementedError

    @abstractmethod
    def self_validate(self):
        """Validates the WeatherModel by validating ...

        Returns:
            The value True if everything was validated successfully and raises an InvalidWeatherModelException if not.
        """
        raise NotImplementedError

    @property
    def valid_request_timeframe(self):
        """A function that return the valid request timeframe for a WeatherModel.

        Returns:
            A Tuple holding the two moments in time in between which at the moment of function call a request could be
            made to the source model in the format (start, end).
        """
        raise NotImplementedError

    @property
    def id(self):
        return self.short_name
