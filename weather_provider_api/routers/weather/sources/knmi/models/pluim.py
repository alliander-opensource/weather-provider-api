# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0 AND CC-BY-2.5

"""KNMI day part prediction data fetcher."""

import copy
from datetime import UTC, datetime, timedelta

import requests  # type: ignore
import xarray as xr
from loguru import logger

from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.sources.knmi.stations import (
    stations_prediction,
)
from weather_provider_api.routers.weather.sources.knmi.utils.commons import find_closest_stn_list
from weather_provider_api.routers.weather.utils.date_helpers import (
    validate_begin_and_end,
)
from weather_provider_api.routers.weather.utils.geo_position import GeoPosition
from weather_provider_api.routers.weather.utils.pandas_helpers import coords_to_pd_index


class PluimModel(WeatherModelBase):
    """A class to fetch the KNMI pluim data, which contains predictions for the coming 15 days."""

    def __init__(self):
        """Initialize the PluimModel with its specific attributes and conversion dictionaries."""
        super().__init__()
        self.id = "pluim"
        logger.debug(f"Initializing weather model [{self.id}]")

        self.name = "ECMWF pluim"
        self.version = ""
        self.url = "https://www.knmi.nl/nederland-nu/weer/waarschuwingen-en-verwachtingen/weer-en-klimaatpluim"
        self.predictive = True
        self.time_step_size_minutes = 720
        self.num_time_steps = 30
        self.description = (
            "Predictions for the coming 15 days, current included, with two predictions made for each day."
        )
        self.async_model = False

        self.to_si = {  # type: ignore
            "wind_speed": {
                "name": "wind_speed",
                "convert": self.kmh_to_ms,  # km/h -> m/s
                "code": 11012,
            },
            "wind_direction": {
                "name": "wind_direction",
                "convert": self.no_conversion,  # 360N, 270W, ...
                "code": 11011,
            },
            "short_time_wind_speed": {
                "name": "wind_speed_max",
                "convert": self.kmh_to_ms,  # km/h -> m/s
                "code": 11041,
            },
            "temperature": {
                "name": "temperature",
                "convert": self.celsius_to_kelvin,  # degree C -> Kelvin
                "code": 99999,
            },
            "precipitation": {
                "name": "precipitation",
                "convert": lambda x: x / 1000,  # mm -> m  # type: ignore
                "code": 13021,
            },
            "precipitation_sum": {
                "name": "precipitation_sum",
                "convert": lambda x: x / 1000,  # mm -> m  # type: ignore
                "code": 13011,
            },
            "cape": {
                "name": "cape",
                "convert": lambda x: x / 1000,  # type: ignore
                "code": 13241,
            },  # J/kg
        }

        self.to_human = copy.deepcopy(self.to_si)  # type: ignore
        self.to_human["temperature"]["convert"] = self.no_conversion  # C -> C  # type: ignore
        self.to_human["precipitation"]["convert"] = self.no_conversion  # mm  # type: ignore
        self.to_human["precipitation_sum"]["convert"] = self.no_conversion  # mm  # type: ignore

        self.human_to_model_specific = self._create_reverse_lookup(self.to_si)  # type: ignore

        logger.debug(f"Weather model [{self.id}] initialized successfully")

    def get_weather(
        self,
        coords: list[GeoPosition],
        begin: datetime | None = None,
        end: datetime | None = None,
        weather_factors: list[str] | None = None,
    ) -> xr.Dataset:
        """Gather and process the requested weather data for the given coordinates, time frame and weather factors.

        The function that gathers and processes the requested Daggegevens weather data from the KNMI site and returns
        it as a Xarray Dataset.
        (Though this model downloads from a specific download url, the question remains whether this source is also
        listed on the new KNMI Data Platform)

        Args:
            coords:             A list of GeoPositions containing the locations the data is requested for.
            begin:              A datetime containing the start of the period to request data for.
            end:                A datetime containing the end of the period to request data for.
            weather_factors:    A list of weather factors to request data for (in string format)

        Returns:
            An Xarray Dataset containing the weather data for the requested period, locations and factors.
        """
        # Test and account for invalid datetime timeframes or input
        begin, end = validate_begin_and_end(begin, end, datetime.now(UTC), datetime.now(UTC) + timedelta(days=15))

        # get list of relevant STNs, choose closest STN
        _, stns, coords_stn_ind = find_closest_stn_list(stations_prediction, coords)

        # load default weather factors if unspecified
        if weather_factors is None:
            weather_factors = self.to_si.keys()  # type: ignore

        # download the weather factors for all stations
        ds = self._download_weather(coords, coords_stn_ind, stns, weather_factors)  # type: ignore

        ds = self._select_weather_from_given_period(ds, begin, end)
        ds = ds.dropna("time", how="all")  # Dropping any times that only carry NaN values

        return ds

    @staticmethod
    def _select_weather_from_given_period(ds: xr.Dataset, begin: datetime | None, end: datetime | None) -> xr.Dataset:
        """A function that filters the given Xarray Dataset to only the requested period.

        Args:
            ds:     An Xarray Dataset to be filtered
            begin:  A datetime containing the start of the period to filter.
            end:    A datetime containing the end of the period to filter.

        Returns:
            An Xarray Dataset containing all the data from the original dataset that matches the given period.
        """
        begin, end = validate_begin_and_end(
            begin,
            end,
            datetime.today().replace(hour=0, minute=0, second=0),
            datetime.today().replace(hour=0, minute=0, second=0) + timedelta(days=15),
        )
        ds = ds.sel(time=slice(begin.astimezone(UTC), end.astimezone(UTC)))
        return ds

    def is_async(self) -> bool:  # pragma: no cover
        """Determine if the model is asynchronous."""
        return self.async_model

    def _download_weather(
        self,
        coordinates: list[GeoPosition],
        coords_stn_ind: list[int],
        stns: list[int],
        weather_factors: list[str],
    ) -> xr.Dataset:
        """A function that downloads the requested weather data, factor by factor, without numpy."""
        arr_dict = {}
        ds = xr.Dataset()
        for weather_factor in weather_factors:
            try:
                code: int = self.to_si[weather_factor]["code"]  # type: ignore
            except KeyError:
                continue

            timeline, values = self._download_single_factor(stns, code)  # type: ignore
            # values: station-major (station, time)
            if not values:
                continue
            time_len = len(timeline)
            station_len = len(values)
            # Transpose: list of lists (time, station)
            values_time_major = [
                [values[stn_idx][t_idx] for stn_idx in range(station_len)] for t_idx in range(time_len)
            ]
            # Select only the stations in coords_stn_ind order
            values_selected = [[row[i] for i in coords_stn_ind] for row in values_time_major]
            mindex_coords = xr.Coordinates.from_pandas_multiindex(coords_to_pd_index(coordinates), "coord")
            arr_dict[weather_factor] = xr.DataArray(
                data=values_selected,
                dims=["time", "coord"],
                coords={"time": timeline, **mindex_coords},
                name=weather_factor,
            )
            ds = xr.merge(arr_dict.values(), join="outer")  # type: ignore
        ds = ds.unstack("coord")
        return ds

    @staticmethod
    def _download_single_stn_factor(stn: int, factor: int) -> tuple[list[datetime], list[float]]:
        """Download a single factor for a single station.

        Args:
            stn:    The station (ID) to download the factor for
            factor: The weather factor to download
        Returns:
            A list of datetime64 items holding the times for the factors, and a matching list of values holding
            values belonging to the requested factor during those times.
        """
        base_url = (
            f"https://cdn.knmi.nl/knmi/json/page/weer/waarschuwingen_verwachtingen/ensemble/iPluim/{stn}_{factor}.json"
        )

        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            raise requests.HTTPError(
                "Failed to retrieve data from the KNMI website",
                response.status_code,
                base_url,
            )

        series = response.json()["series"]
        # only retrieve prediction
        prediction_data = next(x for x in series if "Verwacht" in x["name"])["data"]
        if isinstance(prediction_data[0], dict):
            timeline = [datetime.fromtimestamp(x["x"] / 1000, UTC) for x in prediction_data]
            value = [float(x["y"]) for x in prediction_data]
        else:
            timeline = [datetime.fromtimestamp(x[0] / 1000, UTC) for x in prediction_data]
            value = [float(x[1]) for x in prediction_data]

        return timeline, value

    def _download_single_factor(self, stns: list[int], factor: int) -> tuple[list[datetime], list[list[float]]]:
        """Download a single factor for all the given stations, without numpy.

        Args:
            stns:   A list of stations to download the factor for.
            factor: The weather factor to download.

        Returns:
            A tuple: (timeline, values), where timeline is a list of datetime objects (from the first station),
            and values is a list of lists (station-major: values[station][time]).
        """
        all_values: list[list[float]] = []
        timeline: list[datetime] = []
        for idx, stn in enumerate(stns):
            stn_timeline, stn_values = self._download_single_stn_factor(stn, factor)
            if idx == 0:
                timeline = stn_timeline
            all_values.append(stn_values)
        return timeline, all_values

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
