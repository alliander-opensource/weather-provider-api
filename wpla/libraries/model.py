#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""The MeteoModel

The MeteoModel class is how any and all meteorological data gets gathered and preformatted for use by the project.

"""

import datetime
from abc import abstractmethod
from typing import List, Tuple

import numpy as np
from loguru import logger
from pydantic import AnyHttpUrl
from pyproj import CRS, transform

from wpla.libraries.exceptions.exceptions import (
    TimeFrameOutOfBoundException,
    LocationsOutOfBoundException,
)


class MeteoModel:
    """The MeteoModel class

    This class is used by any by the project's supported models out there. It provides easy and standardized access
    to meteorological data and contains standard functionality for initialisation, validation checks and base interface
    options. This makes creating your own model-class a lot easier, as you can focus on just downloading and
    preformatting the data, as the base class does the rest.

    """

    def __new__(
            cls,
            short_name: str,
            long_name: str,
            description: str,
            license_info: str,
            information_url: AnyHttpUrl,
    ):
        obj = object.__new__(cls)
        obj.short_name = short_name
        obj.long_name = long_name
        obj.description = description
        obj.license_info = license_info
        obj.information_url = information_url
        obj.version_support = "Unknown"
        obj.oldest_day_of_data = None
        obj.newest_day_of_data = None
        obj.update_frequency = None
        obj.grid_type = CRS("EPSG:4326")  # Default is WGS84
        obj.grid_resolution = None
        obj.original_file_format = None
        obj.original_unit_system = None
        obj.factor_table = {}
        return obj

    def is_valid(self):
        """MeteoModel self-check"""
        return_value = True

        # Check 1: validate core data field length:
        dict_to_check = {
            "short_name": 3,  # The short name should consist of at least 3 letters
            "long_name": 8,  # The long name should consist of at least 8 letters
            "description": 20,  # A description should have at least 20 letters in it
            "information_url": 16,  # Even a short URL should usually have at least 16 letters when including 'https://'
            "factor_table": 1,  # At least a single factor should be returned from a MeteoModel
        }

        for key, value in dict_to_check.items():
            if len(getattr(self, key)) <= value:
                logger.warning(f"The length of {key} is less than [{value}]")
                return_value = False

        # Check 2: check for appropriate data types
        if (
                self.oldest_day_of_data is not None
                and not isinstance(self.oldest_day_of_data, datetime.datetime)
        ):
            logger.warning(
                f"The object type of [oldest_day_of_data] is expected to be [datetime.datetime], "
                f"not [{type(self.oldest_day_of_data)}]"
            )
            return_value = False

        if (
                self.newest_day_of_data is not None
                and not isinstance(self.newest_day_of_data, datetime.datetime)
        ):
            logger.warning(
                f"The object type of [newest_day_of_data] is expected to be [datetime.datetime], "
                f"not [{type(self.newest_day_of_data)}]"
            )
            return_value = False

        if self.newest_day_of_data <= self.oldest_day_of_data:
            logger.warning(
                f"The datetime contained in [newest_day_of_data] ({self.newest_day_of_data}) "
                f"does not follow the one in [datetime.oldest_day_of_data] ({self.oldest_day_of_data})."
            )
            return_value = False

        if not isinstance(self.grid_type, CRS):
            logger.warning(
                f"The object type of [grid_type] is expected to be [CRS], not [{type(self.grid_type)}]"
            )
            return_value = False

        if return_value:
            logger.info(
                f"The [{self.long_name}] MeteoModel Class was found valid"
            )
        else:
            logger.info(
                f"The [{self.long_name}] MeteoModel Class was NOT found valid"
            )

        return return_value

    def validate_base_parameters(
            self,
            list_of_coordinates: List[Tuple[np.float64, np.float64]],
            source_crs: CRS,
            oldest_moment: datetime,
            newest_moment: datetime,
    ):
        """Input-validation of base parameters"""
        valid_coordinates, invalid_coordinates = self.validate_coordinates(
            list_of_coordinates, source_crs
        )
        valid_timeframe = self.validate_request_timeframe(
            oldest_moment, newest_moment
        )

        if len(valid_coordinates) == 0:
            raise LocationsOutOfBoundException(
                self.short_name,
                source_crs.name,
                self.grid_type.name,
                invalid_coordinates,
            )

        return valid_coordinates, invalid_coordinates, valid_timeframe

    def validate_coordinates(
            self,
            list_of_coordinates: List[Tuple[np.float64, np.float64]],
            source_crs: CRS,
    ):
        """Input-validation of coordinates"""
        validated_coordinates = []
        invalid_coordinates = []
        for coordinate in list_of_coordinates:
            validated_coordinate = self._validate_coordinate(
                coordinate, source_crs
            )
            if validated_coordinate is not None:
                logger.debug(
                    f"The coordinates ({coordinate[0]}, {coordinate[1]}), resolved as model coordinates "
                    f"({validated_coordinate[0]}, {validated_coordinate[1]})"
                )
                validated_coordinates.append(validated_coordinate)
            else:
                logger.warning(
                    f"The coordinates ({coordinate[0]}, {coordinate[1]}) could not be converted to "
                    f"the model's grid type: {self.grid_type.name}"
                )
                invalid_coordinates.append(coordinate)

        if len(validated_coordinates) == 0:
            raise UnboundLocalError(
                "None of the passed coordinates could be validated!"
            )

        return validated_coordinates, invalid_coordinates

    def _validate_coordinate(
            self, coordinate: Tuple[np.float64, np.float64], source_crs: CRS
    ):
        """The actual validation process of the coordinates between any supported coordinate systems"""
        wgs84_crs = CRS("EPSG:4326")
        wgs84_coordinate = transform(
            source_crs, wgs84_crs, coordinate[0], coordinate[1]
        )

        # Verify validity of coordinate within source grid:
        if (
                wgs84_coordinate[1] < source_crs.area_of_use.west
                or wgs84_coordinate[1] > source_crs.area_of_use.east
                or wgs84_coordinate[0] > source_crs.area_of_use.north
                or wgs84_coordinate[0] < source_crs.area_of_use.south
        ):
            # Invalid coordinate
            logger.debug(
                f"The supplied coordinate {coordinate} was invalid for the source grid: [{source_crs.name}]"
            )
            return None

        # Verify validity of coordinate within target grid:
        if (
                wgs84_coordinate[1] < self.grid_type.area_of_use.west
                or wgs84_coordinate[1] > self.grid_type.area_of_use.east
                or wgs84_coordinate[0] > self.grid_type.area_of_use.north
                or wgs84_coordinate[0] < self.grid_type.area_of_use.south
        ):
            # Invalid coordinate
            logger.debug(
                f"The supplied coordinate {coordinate} was invalid for the target grid: [{self.grid_type.name}]"
            )
            return None

        validated_coordinate = transform(
            wgs84_crs, self.grid_type, wgs84_coordinate[0], wgs84_coordinate[1]
        )
        return validated_coordinate

    def validate_request_timeframe(
            self, oldest_moment: datetime, newest_moment: datetime
    ):
        """Input-validation of the supplied timeframe"""
        validated_oldest_moment = oldest_moment
        validated_newest_moment = newest_moment

        if self.oldest_day_of_data is not None:
            if validated_oldest_moment < self.oldest_day_of_data:
                validated_oldest_moment = self.oldest_day_of_data
                logger.debug(
                    "Corrected starting datetime to oldest datetime in data"
                )

        if self.newest_day_of_data is not None:
            if validated_newest_moment > self.newest_day_of_data:
                validated_newest_moment = self.newest_day_of_data
                logger.debug(
                    "Corrected ending datetime to newest datetime in data"
                )

        if self.oldest_day_of_data >= self.newest_day_of_data:
            raise TimeFrameOutOfBoundException(
                self.short_name,
                (oldest_moment, newest_moment),
                (self.oldest_day_of_data, self.newest_day_of_data),
            )

        return validated_oldest_moment, validated_newest_moment

    @property
    def name(self):
        """Shorthand property for the short_name attribute."""
        return self.short_name

    @abstractmethod
    def get_weather(
            self,
            locations: List[Tuple[np.float64, np.float64]],
            starting: datetime,
            ending: datetime,
            factor_list: List[str],
            source_epsg: str = "4326",
            target_epsg: str = "4326",
            use_nearest_data: bool = False,
            return_used_locations: bool = False,
    ):
        """The core function of this class, that gathers meteorological data based on passed request parameters and
        returns a Xarray Dataset holding the requested data.

        Note: The returned data is not yet harmonized, but can be requested using harmonized factor codes.

        Args:
            locations:              A list of location coordinates to try and gather the weather from.
                                    Note: The function currently assumes purely numerical coordinate systems.
            starting:               A datetime object holding the oldest moment from which data should be gathered.
            ending:                 A datetime object holding the newest moment from which data should be gathered.
            factor_list:            A list of weather factors to gather in string format.
                                    Both harmonized and unharmonized factor names are supported.
            source_epsg:            An optional EPSG coordinate system ID. Used to determine the location of the
                                    supplied list of locations. The default is the WGS84 coordinate system.
            target_epsg:            An optional EPSG coordinate system ID. Used to determine the format of the
                                    returned list of locations. The default is the WGS84 coordinate system.
            use_nearest_data:       A boolean indicating whether the returned data should contain the data found at the
                                    location closest to a location (True), or data created for the exact location by
                                    using an interpolation system, if supported (False, Default value).
            return_used_locations:  A boolean indicating whether to append the locations used to the return data when
                                    using the nearest data, rather than using interpolation.
                                    Note: Only has any effect when the model uses nearby data instead of interpolated
                                    data.

        Returns:
            A Xarray Dataset, fully harmonized and formatted with the data as requested.

        """
        return NotImplementedError
