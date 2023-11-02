#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from abc import ABCMeta, abstractmethod
from typing import List, Optional

import numpy as np
import xarray as xr

from weather_provider_api.core.initializers.exception_handling import NOT_IMPLEMENTED_ERROR
from weather_provider_api.routers.weather.api_models import OutputUnit
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class WeatherModelBase(metaclass=ABCMeta):
    """
    Base class for all Weather Models. All new models should use this base class!
    """

    def __init__(self):
        self.to_si = None
        self.to_human = None
        self.human_to_model_specific = None

    @abstractmethod
    def get_weather(
        self,
        coords: List[GeoPosition],
        begin: Optional[np.datetime64],
        end: Optional[np.datetime64],
        weather_factors: List[str] = None,
    ) -> xr.Dataset:  # pragma: no cover
        raise NotImplementedError(NOT_IMPLEMENTED_ERROR)

    @abstractmethod
    def is_async(self):  # pragma: no cover
        raise NotImplementedError(NOT_IMPLEMENTED_ERROR)

    def convert_names_and_units(self, weather_data: xr.Dataset, unit: OutputUnit):
        """
            Function to convert all names and units in a dataset according to the required translations set in the
            to_xxxx values for the model itself
        Args:
            weather_data:   A Xarray Dataset containing
            unit:           The requested output unit format

        Returns:
            The same dataset, but with values altered to match the requested output unit format
        """
        if unit == OutputUnit.original:
            return weather_data

        if unit == OutputUnit.si:
            conversion_dict = self.to_si
        elif unit == OutputUnit.human:
            conversion_dict = self.to_human
        else:
            raise TypeError("Invalid OutputUnit")

        data_vars = list(weather_data.data_vars)
        for var_name in data_vars:
            if var_name not in data_vars or var_name not in conversion_dict:
                continue

            new_name = var_name
            if "name" in conversion_dict[var_name]:
                new_name = conversion_dict[var_name]["name"]

            new_data = weather_data[var_name]
            if "convert" in conversion_dict[var_name]:
                converter: callable = conversion_dict[var_name]["convert"]
                new_data = converter(weather_data[var_name])

            weather_data = weather_data.drop_vars(var_name)
            weather_data[new_name] = new_data

        return weather_data

    @staticmethod
    def _create_reverse_lookup(conversion_dict):  # pragma: no cover
        reverse = dict()

        for k, v in conversion_dict.items():
            if "name" in v:
                reverse[v["name"]] = k

        return reverse

    @abstractmethod
    def _request_weather_factors(self, factors: Optional[List[str]]) -> List[str]:
        raise NotImplementedError(NOT_IMPLEMENTED_ERROR)

    @staticmethod
    def celsius_to_kelvin(x):  # pragma: no cover
        return x + 273.15

    @staticmethod
    def kelvin_to_celsius(x):  # pragma: no cover
        return x - 273.15

    def tenth_celsius_to_kelvin(self, x):  # pragma: no cover
        return self.celsius_to_kelvin(self.normalize_tenths(x))

    @staticmethod
    def normalize_tenths(x):  # pragma: no cover
        return x / 10

    @staticmethod
    def no_conversion(x):  # pragma: no cover
        return x

    @staticmethod
    def percentage_to_frac(x):  # pragma: no cover
        return x / 100

    @staticmethod
    def kmh_to_ms(x):  # pragma: no cover
        return x / 3.6

    @staticmethod
    def dutch_wind_direction_to_degrees(xs):

        wind_directions = [
            "NNO",
            "NO",
            "ONO",
            "O",
            "OZO",
            "ZO",
            "ZZO",
            "Z",
            "ZZW",
            "ZW",
            "WZW",
            "W",
            "WNW",
            "NW",
            "NNW",
            "N",
        ]

        def dutch_wind_direction_to_degrees_single(x):
            if x in wind_directions:
                return (wind_directions.index(x) + 1) * 22.5
            else:
                return None

        return np.frompyfunc(dutch_wind_direction_to_degrees_single, 1, 1)(xs)

    @staticmethod
    def knmi_visibility_class_to_meter_estimate(xs):
        """
            Function to transform KNMI visibility class values to an estimate of meters visibility
        Args:
            xs:     The visibility class value to be interpreted

        Returns:
            A numeric value containing an estimate of the meters of visibility matching the given visibility class value

        """

        def knmi_visibility_class_to_meter_estimate_single(x):
            if x < 50:
                return x * 100 + 50
            elif x == 50:
                return 5500
            elif x < 80:
                return (x - 50) * 1000 + 500
            elif x < 89:
                return (x - 80) * 5000 + 30000 + 2500
            else:
                # Even though the value 0f 88 results in 72500 as a return value, the final return of 70000 is correct.
                # From 80 up to 88 each return represents a value range of 5000, and for 88 this is 70000 - 75000,
                # represented by 72500. From 89 up the value is given as "more than 70000", which is why 70000 is
                # returned from then on.
                return 70000

        return np.frompyfunc(knmi_visibility_class_to_meter_estimate_single, 1, 1)(xs)
