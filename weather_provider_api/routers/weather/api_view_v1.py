#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""
TODO:
- Decouple weather factors from the get_weather function
- Add the async process for e.g. CDS and Harmonie
- Improve datetime slicing
- Fix datetime validation in Swagger UI on IE and Safari
- Improve output / error messages when no data is available
"""

from typing import List

import accept_types
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException

from weather_provider_api.routers.weather.api_models import (
    WeatherContentRequestQuery,
    WeatherFormattingRequestQuery,
    WeatherModel,
    WeatherSource,
    result_mime_types,
)
from weather_provider_api.routers.weather.controller import WeatherController
from weather_provider_api.routers.weather.sources.weather_alert.weather_alert import WeatherAlert
from weather_provider_api.routers.weather.utils import serializers
from weather_provider_api.routers.weather.utils.date_helpers import parse_datetime
from weather_provider_api.routers.weather.utils.file_helpers import remove_file

app = APIRouter()

controller = WeatherController()


def header_accept_type(accept: str = Header(None)) -> str:
    # Matches the given string to the nearest result in result_mime_types and returns the matching value
    best_match_or_none = accept_types.get_best_match(accept, result_mime_types)
    return result_mime_types[best_match_or_none]


# @weather_provider_api.get("/sources", response_model=List[WeatherSource], tags=["sync", "async"])
@app.get("/sources", response_model=List[WeatherSource], tags=["sync"])
async def get_sources():  # pragma: no cover
    # List all the sources known by the controller
    return controller.get_sources()


# @weather_provider_api.get("/sources/{source_id}", response_model=WeatherSource, tags=["sync", "async"])
@app.get("/sources/{source_id}", response_model=WeatherSource, tags=["sync"])
async def get_source(source_id: str):  # pragma: no cover
    # List all the models supported by the selected source
    source_id = source_id.lower()
    return controller.get_source(source_id)


@app.get("/sources/{source_id}/models", response_model=List[WeatherModel], tags=["sync"])
async def get_sync_models(source_id: str):  # pragma: no cover
    # List all the synchronous models supported by the selected source
    source_id = source_id.lower()
    return controller.get_models(source_id, fetch_async=False)


@app.get("/sources/{source_id}/models/{model_id}", tags=["sync"])
async def get_sync_weather(
    source_id: str,
    model_id: str,
    cleanup_tasks: BackgroundTasks,
    ret_args: WeatherContentRequestQuery = Depends(),
    fmt_args: WeatherFormattingRequestQuery = Depends(),
    accept: str = Depends(header_accept_type),
):  # pragma: no cover
    """
        Function to gather data for a specific model using specific settings (location, period, factors, e.g.).
        The function then formats this data into the requested output format (file-format and selected output unit) and
        returns it.
    Args:
        source_id:  The identifier for the chosen source
        model_id:   The identifier for the chosen model
        cleanup_tasks: Holder for background tasks, in get_sync_weather solely used for file cleanup, hence the name
        ret_args:   Contains a WeatherContentRequestQuery item with all the settings to be used for data collection
        fmt_args:   Contains a WeatherFormattingRequestQuery item with all the setting to be used for formatting the
                    output
        accept:

    Returns:
        Returns a file in the requested output format, containing any weather data that matched the specifications from
        the WeatherContentRequestQuery.

    """

    # TODO: Append a proper definition of the accept arg
    source_id = source_id.lower()
    model_id = model_id.lower()
    coords = controller.lat_lon_to_coords(ret_args.lat, ret_args.lon)

    begin = parse_datetime(ret_args.begin, raise_errors=True, loc=["query", "begin"])
    end = parse_datetime(
        ret_args.end,
        round_missing_time_up=True,
        raise_errors=True,
        loc=["query", "end"],
    )

    try:
        weather_data = controller.get_weather(
            source_id,
            model_id,
            fetch_async=False,
            coords=coords,
            begin=begin,
            end=end,
            factors=ret_args.factors,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.args[0])

    if weather_data is None:
        raise HTTPException(status_code=404, detail="No data was found for the given period")

    response_format = fmt_args.response_format or accept

    converted_weather_data = controller.convert_names_and_units(
        source_id, model_id, False, weather_data, fmt_args.units
    )

    coords = [
        (lat_val, lon_val)
        for (lat_val, lon_val) in zip(
            converted_weather_data.coords["lat"].values,
            converted_weather_data.coords["lon"].values,
        )
    ]

    response, optional_file_path = serializers.file_or_text_response(
        converted_weather_data, response_format, source_id, model_id, ret_args, coords
    )
    cleanup_tasks.add_task(remove_file, optional_file_path)

    return response


# @weather_provider_api.get("/weeralarm")
@app.get("/alarms/knmi", tags=["alerts"])
async def get_alarm():  # pragma: no cover
    # Fetches the WeatherAlarm status for all the provinces from KNMI Weer Alarm and returns the results
    weather_alert = WeatherAlert()
    return weather_alert.get_alarm()
