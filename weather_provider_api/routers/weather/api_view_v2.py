#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

"""
"""
from datetime import datetime
from typing import List

import accept_types
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from loguru import logger

from weather_provider_api.core.initializers.rate_limiter import API_RATE_LIMITER
from weather_provider_api.routers.weather.api_models import (
    WeatherContentRequestMultiLocationQuery,
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

v2_router = APIRouter()

controller = WeatherController()


def header_accept_type(accept: str = Header(None)) -> str:
    # Matches the given string to the nearest result in result_mime_types and returns the matching value
    best_match_or_none = accept_types.get_best_match(accept, result_mime_types)
    return result_mime_types[best_match_or_none]


# @weather_provider_api.get("/sources", response_model=List[WeatherSource], tags=["sync", "async"])
@v2_router.get("/sources", response_model=List[WeatherSource], tags=["sync"])
async def get_sources():  # pragma: no cover
    """<B>List all the Weather Sources available</B>"""
    """
        An API function that returns all of the Sources available from the WeatherController
    Args:
        None
    Returns:
        A list of all Source available from the WeatherController
    """
    return controller.get_sources()


# @weather_provider_api.get("/sources/{source_id}", response_model=WeatherSource, tags=["sync", "async"])
@v2_router.get("/sources/{source_id}", response_model=WeatherSource, tags=["sync"])
async def get_source(source_id: str):  # pragma: no cover
    """<B>List all the Models available  for the Source</B>"""
    """
        An API function that returns all of the models available for the given source  
    Args:
        source_id: The source ID for the given source
    Returns:
        A list of all Models available for the given source
    """
    source_id = source_id.lower()
    return controller.get_source(source_id)


@v2_router.get("/sources/{source_id}/models", response_model=List[WeatherModel], tags=["sync"])
async def get_sync_models(source_id: str):  # pragma: no cover
    """<B>List all the synchronous Models available for the selected Source</B>"""
    """
        An API function that returns all of the synchronous models available for the given source
    Args:
        source_id: The source ID for the given source
    Returns:
        A list of all synchronous Models available for the given source
    """

    source_id = source_id.lower()
    return controller.get_models(source_id, fetch_async=False)


@v2_router.get("/sources/{source_id}/models/{model_id}", tags=["sync"])
@API_RATE_LIMITER.limit("20/minute")
async def get_sync_weather(
    request: Request,
    source_id: str,
    model_id: str,
    cleanup_tasks: BackgroundTasks,
    ret_args: WeatherContentRequestQuery = Depends(),
    fmt_args: WeatherFormattingRequestQuery = Depends(),
    accept: str = Depends(header_accept_type),
):  # pragma: no cover
    """
    <B>Request weather data for a specific Model using the given settings (location, period, weather factors, e.g.). <BR>
    This data is then formatted as the requested output format (output unit system and file format) before returning the requested data.</B>

    <I>(Please note that as some models are predictive or otherwise restricted in the periods available for requests,
    that sometimes the 'begin' and 'end' values will be altered to match these restrictions.)</I>
    """
    """
        An API function that retrieves specific weather data for a specific Weather Model and returns it as the
        requested output format and units.
    Args:
        source_id:      The Source ID of the Source to request the weather data from.
        model_id:       The Model ID for the Model to request the weather data from.
        cleanup_tasks:  A BackgroundTasks object to hold any pending cleanup tasks for when the data request is
                        finished.
        ret_args:       A WeatherContentRequestQuery object holding the parameters for the weather data request to
                        use.
        fmt_args:       A WeatherFormattingRequestQuery object holding the parameters for the output format and
                        units to use.
        accept:         Header type to use for the output file.
                        Rounded to the most likely value using header_accept_type().
    Returns:
        The weather data in the requested format for the requested parameters.
    """
    starting_time = datetime.utcnow()
    logger.info(f"WeatherRequest({starting_time}): {request.url}")
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
    logger.info(f"WeatherRequest({starting_time}) data preparation finished.")
    return response


# @weather_provider_api.get("/weeralarm")
@v2_router.get("/alarms/knmi", tags=["alerts"])
async def get_alarm():  # pragma: no cover
    """<B>Fetches the WeatherAlarm status for all the provinces from KNMI Weer Alarm and returns the results</B>"""
    """
        An API Function that reads the status of the Weer Alarm pages on the KNMI Site and returns them.
    Returns:
        A formatted text containing the current Weather Alert Status for each of the provinces.
    """
    weather_alert = WeatherAlert()
    return weather_alert.get_alarm()


# Handler for requests with multiple locations:
@v2_router.get("/sources/{source_id}/models/{model_id}/multiple-locations/", tags=["sync"])
@API_RATE_LIMITER.limit("5/minute")
async def get_sync_weather_multi_loc(
    request: Request,
    source_id: str,
    model_id: str,
    cleanup_tasks: BackgroundTasks,
    ret_args: WeatherContentRequestMultiLocationQuery = Depends(),
    fmt_args: WeatherFormattingRequestQuery = Depends(),
    accept: str = Depends(header_accept_type),
):  # pragma: no cover
    starting_time = datetime.utcnow()
    logger.info(f"WeatherRequest({starting_time}): {request.url}")

    source_id = source_id.lower()
    model_id = model_id.lower()

    coords = controller.str_to_coords(ret_args.locations)

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

    new_coords = []
    for coord in coords:
        new_coords.append(coord[0])

    response, optional_file_path = serializers.file_or_text_response(
        converted_weather_data, response_format, source_id, model_id, ret_args, coords
    )
    cleanup_tasks.add_task(remove_file, optional_file_path)
    logger.info(f"WeatherRequest({starting_time}) data preparation finished.")
    return response
