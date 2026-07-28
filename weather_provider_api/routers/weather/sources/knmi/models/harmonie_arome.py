# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0 AND CC-BY-2.5

"""Module containing the Harmonie Arome Weather Model."""

import copy
from datetime import datetime, time, timedelta

import xarray as xr
from loguru import logger

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.base_models.repository import RepoDataFetchResult
from weather_provider_api.routers.weather.sources.knmi.client.arome_repository import (
    HarmonieAromeRepository,
)
from weather_provider_api.routers.weather.sources.knmi.knmi_factors import arome_factors
from weather_provider_api.routers.weather.utils.date_helpers import (
    validate_begin_and_end,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition


class HarmonieAromeModel(WeatherModelBase):
    """Model class for the 'KNMI - Harmonie Arome' weather dataset.

    A weather model that incorporates the 'KNMI - Harmonie Arome' weather dataset into the Weather Provider
    Libraries and API.

    'KNMI - Harmonie Arome' is a predictive model for the upcoming 48 hours that gets generated every 6 hours.
    """

    def __init__(self):
        """Initialize the Harmonie Arome Weather Model with its specific settings and conversion dictionaries."""
        # Pre-work
        super().__init__()
        self.id = "arome"
        logger.debug(f"Initializing weather model: {self.id}")

        # Setting the model
        self.repository = HarmonieAromeRepository()
        self.name = "harmonie_arome_cy_p1"
        self.version = "0.3"
        self.url = "ftp://data.knmi.nl/download/harmonie_arome_cy40_p1/0.2/"
        self.predictive = True
        self.time_step_size_minutes = 60
        self.num_time_steps = 48
        self.async_model = False
        self.dataset_name = "harmonie_arome_cy40_p1"
        self.dataset_version = "0.2"

        # Put up conversion settings
        si_conversion_dict = {  # type: ignore
            k: {"name": k, "convert": lambda x: x}  # type: ignore
            for k in arome_factors.values()  # type: ignore
        }  # The default output format for Arome is SI
        self.to_si = si_conversion_dict  # type: ignore

        # Human output conversion:
        self.to_human = copy.deepcopy(self.to_si)  # type: ignore
        self.to_human["temperature"]["convert"] = self.kelvin_to_celsius  # type: ignore

        # Initialization complete
        logger.debug(f'The Weather model "{self.id}" was successfully initialized')

    def get_weather(
        self,
        coords: list[GeoPosition],
        begin: datetime | None = None,
        end: datetime | None = None,
        weather_factors: list[str] | None = None,
    ) -> xr.Dataset:
        """Get weather data for the specified coordinates and time range."""
        # Handle possibly missing values for this model
        begin = begin or datetime.combine(datetime.today(), time.min)  # Fallback: start of today
        end = end or datetime.combine(datetime.today() + timedelta(days=1), time.max)  # Fallback: end of tomorrow

        # Validate the given timeframe
        valid_begin, valid_end = validate_begin_and_end(
            begin,
            end,
            self.repository.oldest_date_available,
            self.repository.newest_date_available,
        )

        # Determine which weather factors to request based on the given list and the known factors for this model
        translated_factors: list[str] = []
        if weather_factors is not None and len(weather_factors) > 0:
            for factor in weather_factors:
                if factor in arome_factors.keys():
                    new_factor = arome_factors[factor]
                elif factor in arome_factors.values():
                    new_factor = factor
                else:
                    new_factor = None

                if new_factor is not None and new_factor not in translated_factors:
                    translated_factors.append(new_factor)

        # Gather the period from the repository
        weather_dataset, fetch_result = self.repository.retrieve_data(
            from_date=valid_begin.date(),
            to_date=valid_end.date(),
            locations=[coord.as_wgs84 for coord in coords],
            factors=translated_factors,
        )
        if fetch_result == RepoDataFetchResult.NO_DATA_AVAILABLE or weather_dataset is None:
            logger.info(f"No data available for the requested period ({valid_begin} to {valid_end})")
            return xr.Dataset()  # Return an empty dataset if no data is available

        # Slice the dataset to the exact requested time range
        weather_dataset = weather_dataset.sel(time=slice(valid_begin, valid_end))

        return weather_dataset

    def is_async(self) -> bool:
        """Determine if the model is asynchronous."""
        return self.async_model

    def _request_weather_factors(self, factors: list[str] | None = None) -> list[str]:
        """Return a list of the known weather factors out of a given list for this model.

        Implementation of the Weather Model Base function that returns a list of the known weather factors out of
        a given list for this model.
        """
        if not factors:
            return list(self.to_si.keys())  # type: ignore

        validated_factors = []

        for factor in factors:
            factor_lowercase = factor.lower()

            if factor_lowercase in self.to_si:  # type: ignore
                validated_factors.append(factor_lowercase)  # type: ignore
            elif factor in self.to_si:  # type: ignore
                validated_factors.append(factor)  # type: ignore

        return list(set(validated_factors))  # type: ignore
