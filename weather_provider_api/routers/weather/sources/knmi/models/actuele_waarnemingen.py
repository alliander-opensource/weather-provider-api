# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0 AND CC-BY-2.5

"""KNMI current weather data fetcher."""

import copy
from datetime import datetime

import xarray as xr
from loguru import logger

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.sources.knmi.stations import (
    stations_actual,
)
from weather_provider_api.routers.weather.sources.knmi.utils.commons import (
    download_actuele_waarnemingen_weather,
    find_closest_stn_list,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.pandas_helpers import coords_to_pd_index


class ActueleWaarnemingenModel(WeatherModelBase):
    """A model for fetching the current weather data from the KNMI "Actuele Waarnemingen" dataset."""

    def __init__(self):
        """Initialize the Actuele Waarnemingen model with its specific properties and conversion dictionaries."""
        super().__init__()
        self.id = "waarnemingen"
        self.name = "KNMI Actuele Waarnemingen"
        self.version = ""
        self.url = "https://www.knmi.nl/nederland-nu/weer/waarnemingen"
        self.predictive = False
        self.time_step_size_minutes = 10
        self.num_time_steps = 1
        self.description = "Current weather observations. Updated every 10 minutes."
        self.async_model = False

        self.to_si = {  # type: ignore
            "weather_description": {
                "name": "weather_description",
                "convert": self.no_conversion,
            },
            "temperature": {"convert": self.celsius_to_kelvin},
            "humidity": {"convert": self.percentage_to_frac},
            "wind_direction": {"convert": self.dutch_wind_direction_to_degrees},
            "wind_speed": {"convert": self.no_conversion},  # m/s
            "visibility": {"convert": self.no_conversion},  # m
            "air_pressure": {"convert": lambda x: x * 100},  # hPa to Pa  # type: ignore
        }
        self.to_human = copy.deepcopy(self.to_si)  # type: ignore
        self.to_human["temperature"]["convert"] = self.no_conversion  # C  # type: ignore

        self.human_to_model_specific = self._create_reverse_lookup(self.to_si)  # type: ignore

    def get_weather(
        self,
        coords: list[GeoPosition],
        begin: datetime | None = None,
        end: datetime | None = None,
        weather_factors: list[str] | None = None,
    ) -> xr.Dataset:
        """Gather and process the requested Actuele Waarnemingen weather data from the KNMI site and return it as a Xarray Dataset.

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

        Notes:
            As this model only return the current weather data the 'begin' and 'end' values are not actually used.
        """
        logger.debug(
            "Starting retrieval of KNMI Actuele Waarnemingen data for requested coordinates and weather factors."
        )
        updated_weather_factors = self._request_weather_factors(weather_factors)

        # Download the current weather data
        raw_ds = download_actuele_waarnemingen_weather()

        # Get a list of the relevant STNs and choose the closest STN for each coordinate
        coords_stn, _, _ = find_closest_stn_list(stations_actual, coords)

        # Select the data for the found closest STNs
        ds = raw_ds.sel(STN=coords_stn)  # type: ignore

        data_dict = {  # type: ignore
            var_name: (["time", "coord"], var.values)  # type: ignore
            for var_name, var in ds.data_vars.items()  # type: ignore
            if var_name in updated_weather_factors and var_name not in ["lat", "lon"]
        }

        timeline = ds.coords["time"].values  # type: ignore

        coord_index = coords_to_pd_index(coords)
        mindex_coords = xr.Coordinates.from_pandas_multiindex(coord_index, "coord")

        ds = xr.Dataset(
            data_vars=data_dict,  # type: ignore
            coords={"time": timeline, **mindex_coords},
        )
        ds = ds.unstack("coord")

        logger.debug("Finished processing KNMI Actuele Waarnemingen data and returning dataset.")
        return ds

    def is_async(self) -> bool:  # pragma: no cover
        """Determine if the model is asynchronous. For the Actuele Waarnemingen model, this returns False as it is a synchronous model."""
        return self.async_model

    def _request_weather_factors(self, factors: list[str] | None = None) -> list[str]:
        # Implementation of the Base Weather Model function that returns a list of known weather factors for the model.
        if factors is None:
            return list(self.to_si.keys())  # type: ignore

        new_factors = []

        for f in factors:
            f_low = f.lower()
            if f_low in self.to_si:  # type: ignore
                new_factors.append(f_low)  # type: ignore

        return list(set(new_factors))  # Cleanup any duplicate values and return  # type: ignore
