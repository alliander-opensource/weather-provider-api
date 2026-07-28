# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""CDS - ERA5 Single Levels Weather data Model."""

import copy
from datetime import datetime

import numpy as np
import xarray as xr
from loguru import logger

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.base_models.repository import RepoDataFetchResult
from weather_provider_api.routers.weather.sources.cds.client.era5sl_repository import (
    ERA5SLRepository,
)
from weather_provider_api.routers.weather.sources.cds.factors import era5sl_factors
from weather_provider_api.routers.weather.utils.date_helpers import (
    validate_begin_and_end,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class ERA5SLModel(WeatherModelBase):
    """A weather model for the CDS ERA5 Single Levels dataset."""

    def __init__(self):
        """Initializes the ERA5SLModel with its specific configuration and repository."""
        super().__init__()
        self.id = "era5sl"
        logger.debug(f"Initializing weather model [{self.id}]")

        self.name = "CDS ERA5 - Hourly data on single levels from 1979 to the present"

        self.version = "0.3"
        self.url = "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview"
        self.predictive = False
        self.description = (
            "Hourly weather measurements. Can be returned for a specified period. The number of "
            "measurements returned depends on this period selection."
        )
        self.async_model = False

        self.time_step_size_minutes = 60
        self.num_time_steps = 0

        self.repository = ERA5SLRepository()

        # Set up Conversion Dictionary
        si_conversion_dict = {  # type: ignore
            k: {"name": k, "convert": lambda x: x}  # type: ignore
            for k in era5sl_factors.values()  # type: ignore
        }  # The default output format for ERA5SL is already SI
        self.to_si = si_conversion_dict  # type: ignore

        # Human output conversion:
        self.to_human = copy.deepcopy(self.to_si)  # type: ignore
        self.to_human["soil_temperature_level_1"]["convert"] = self.kelvin_to_celsius  # type: ignore
        self.to_human["soil_temperature_level_2"]["convert"] = self.kelvin_to_celsius  # type: ignore
        self.to_human["soil_temperature_level_3"]["convert"] = self.kelvin_to_celsius  # type: ignore
        self.to_human["soil_temperature_level_4"]["convert"] = self.kelvin_to_celsius  # type: ignore
        self.to_human["2m_temperature"]["convert"] = self.kelvin_to_celsius  # type: ignore

        logger.debug(f"Weather model [{self.id}] initialized successfully")

    def is_async(self) -> bool:
        """Returns whether the model is asynchronous or not."""
        return self.async_model

    def get_weather(
        self,
        coords: list[GeoPosition],
        begin: datetime | None = None,
        end: datetime | None = None,
        weather_factors: list[str] | None = None,
    ) -> xr.Dataset:
        """Gather and process the requested ERA5SL weather data from the repository, and return it as a Xarray Dataset.

        The function that gathers and processes the requested ERA5 Single Levels weather data from the repository
            and returns it as a Xarray Dataset.

        Args:
            coords:             A list of GeoPositions containing the locations the data is requested for.
            begin:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            weather_factors:    A list of weather factors to request data for (in string format)

        Returns:
            An Xarray Dataset containing the weather data for the requested period, locations and factors.
        """
        # Test and account for invalid datetime timeframes or input
        begin, end = validate_begin_and_end(
            begin,
            end,
            self.repository.oldest_date_available,
            self.repository.newest_date_available,
        )

        # Validate the requested weather factors:
        validated_factors = self._validate_weather_factors(weather_factors)

        ds = self._fill_dataset_with_data(coords, begin, end, validated_factors)
        return ds

    @staticmethod
    def _validate_weather_factors(weather_factors: list[str] | None) -> list[str]:
        """Validate the requested weather factors against those available in the ERA5SL dataset.

        A function that validates a list of weather factors to that of the dataset in the repository.
            Existing factors will be kept, non-existing removed, and if the list is empty the full set for the dataset
            will be used.

        Args:
            weather_factors:    A list of weather factors to validate (in string format)

        Returns:
            A list of weather factors (in string format) only factors that match those of the ERA5SL dataset.
        """
        if weather_factors is None:
            weather_factors = [era5sl_factors[x] for x in era5sl_factors.keys()]

        # Lookup using the generic long name
        weather_factors_long_names = [x for x in weather_factors if x in era5sl_factors.values()]
        # Lookup using the CDS' own short name
        weather_factors_short_names = [era5sl_factors[x] for x in weather_factors if x in era5sl_factors.keys()]

        # Merge the results
        weather_factors = weather_factors_long_names + weather_factors_short_names

        # If nothing useful was found, just return everything
        return weather_factors

    @staticmethod
    def _get_list_of_factors_to_drop(factors: list[str]) -> list[str]:
        """Compare a list of factors to keep with the full list, to make a list of factors to drop from a full set."""
        to_drop = [x for x in era5sl_factors.values() if x not in factors]
        logger.debug("Dropping the following factors for the request: " + str(to_drop))
        return to_drop

    def _fill_dataset_with_data(
        self,
        era5sl_coordinates: list[GeoPosition],
        begin: datetime,
        end: datetime,
        validated_factors: list[str],
    ) -> xr.Dataset:
        """Fill a dataset with ERA5SL weather data from the repository, based on the requested coordinates and period.

        A function that fills a dataset with ERA5SL weather data from the repository, based on the requested
            coordinates and period, and removes any not-requested weather factors from the output.

        Args:
            era5sl_coordinates:     A list of GeoPositions containing the locations to be gathered from the repository.
            begin:                  A datetime containing the starting moment for the period to gather.
            end:                    A datetime containing the end moment for the period to gather.
            validated_factors:      A list of valid ERA5SL factors wanted for the result.

        Returns:
            An Xarray Dataset containing the weather data requested.
        """
        # Gather a dataset with the proper period and coordinates
        arome_dataset, fetch_result = self.repository.retrieve_data(
            from_date=begin.date(),
            to_date=end.date(),
            locations=[coordinate.as_wgs84 for coordinate in era5sl_coordinates],
            factors=validated_factors,
        )

        if fetch_result == RepoDataFetchResult.FAILURE or arome_dataset is None:
            logger.error("Failed to retrieve data from the repository for the given request parameters.")
            raise RuntimeError("Data retrieval failure")

        arome_dataset = arome_dataset.sel(time=slice(np.datetime64(begin), np.datetime64(end)))

        # Drop excess weather factors
        arome_dataset = arome_dataset.drop_vars(self._get_list_of_factors_to_drop(validated_factors))
        return arome_dataset

    def _request_weather_factors(self, factors: list[str] | None = None) -> list[str]:
        """A function that gathers the requested weather factors, validates them, and returns them."""
        # Implementation of the Base Weather Model function that returns a list of known weather factors for the model.
        if factors is None:
            return list(self.to_si.keys())  # type: ignore

        new_factors = []

        for f in factors:
            f_low = f.lower()

            if f_low in self.to_si:  # type: ignore
                new_factors.append(f_low)  # type: ignore

        return list(set(new_factors))  # Cleanup any duplicate values and return  # type: ignore
