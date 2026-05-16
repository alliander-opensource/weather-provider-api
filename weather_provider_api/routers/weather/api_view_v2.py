#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from datetime import UTC, datetime
from typing import Annotated, List

import accept_types  # type: ignore
import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, Response
from loguru import logger

from weather_provider_api.core.initializers.rate_limiter import API_RATE_LIMITER
from weather_provider_api.routers.weather.api_models import ResponseFormat, ScientificJSONResponse, WeatherContentRequestMultiLocationQuery, WeatherContentRequestQuery, WeatherFormattingRequestQuery, WeatherModel, WeatherSource, get_weather_content_request_query, get_weather_formatting_request_query, result_mime_types
from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.base_models.source import WeatherSourceBase
from weather_provider_api.routers.weather.controller import WeatherController
from weather_provider_api.routers.weather.sources.weather_alert.weather_alert import (
    WeatherAlert,
)
from weather_provider_api.routers.weather.utils import serializers
from weather_provider_api.routers.weather.utils.date_helpers import parse_datetime
from weather_provider_api.routers.weather.utils.file_helpers import remove_file

v2_router = APIRouter()

controller = WeatherController()


def header_accept_type(accept: str = Header(None)) -> ResponseFormat:
    """Match the given string to the nearest result in result_mime_types and returns the matching value."""
    best_match_or_none = str(accept_types.get_best_match(accept, result_mime_types))  # type: ignore
    return result_mime_types[best_match_or_none]


# @weather_provider_api.get("/sources", response_model=List[WeatherSource], tags=["sync", "async"])
@v2_router.get("/sources", response_model=List[WeatherSource], tags=["sync"])
async def get_sources() -> list[WeatherSourceBase]:  # pragma: no cover
    """List all of the Weather Sources available.
    
    An API route that returns a list of all the Weather Sources available from the WeatherController. 
    Each Source contains information about the source and a list of the Models available for that Source.

    Args:
        None
    Returns:
        A list of all Source available from the WeatherController
    """
    return controller.get_sources()


# @weather_provider_api.get("/sources/{source_id}", response_model=WeatherSource, tags=["sync", "async"])
@v2_router.get("/sources/{source_id}", response_model=WeatherSource, tags=["sync"])
async def get_source(source_id: str) -> WeatherSourceBase | None:  # pragma: no cover
    """List all the Models available  for the Source.
        
    An API route that returns a list of all the Models available for the given Source ID.

    Args:
        source_id: The source ID for the given source
    Returns:
        A list of all Models available for the given source
    """
    source_id = source_id.lower()
    return controller.get_source(source_id)


@v2_router.get("/sources/{source_id}/models", response_model=List[WeatherModel], tags=["sync"])
async def get_sync_models(source_id: str) -> list[WeatherModelBase]:  # pragma: no cover
    """List all the synchronous Models available for the selected Source.

    An API function that returns all of the synchronous models available for the given source.

    Args:
        source_id: The source ID for the given source
    Returns:
        A list of all synchronous Models available for the given source
    """
    source_id = source_id.lower()
    return controller.get_models(source_id, fetch_async=False)


@v2_router.get(
    "/sources/{source_id}/models/{model_id}",
    tags=["sync"],
    responses={
        200: {"description": "Successful response with the requested weather data."},
        404: {"description": "No data was found for the given period or file not found."},
        422: {"description": "Invalid or missing query parameters."},
    },
    response_class=ScientificJSONResponse,
)
@API_RATE_LIMITER.limit("20/minute")  # type: ignore
async def get_sync_weather(
    request: Request,
    source_id: str,
    model_id: str,
    cleanup_tasks: BackgroundTasks,
    ret_args: Annotated[WeatherContentRequestQuery, Depends(get_weather_content_request_query)],
    fmt_args: Annotated[WeatherFormattingRequestQuery, Depends(get_weather_formatting_request_query)],
    accept: Annotated[ResponseFormat, Depends(header_accept_type)],
) -> Response:  # pragma: no cover
    """Request weather data for a specific Model using the given settings (location, period, weather factors, e.g.).
    
    This data is then formatted as the requested output format (output unit system and file format) before returning the requested data.

    (Please note that as some models are predictive or otherwise restricted in the periods available for requests,
    that sometimes the 'begin' and 'end' values will be altered to match these restrictions.)
    An API function that retrieves specific weather data for a specific Weather Model and returns it as the
    requested output format and units.

    Args:
        request:        The original request object containing query parameters.
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
    starting_time = datetime.now(tz=UTC)
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
        raise HTTPException(status_code=404, detail=e.args[0]) from e

    if weather_data is None:
        raise HTTPException(status_code=404, detail="No data was found for the given period")

    response_format = fmt_args.response_format or accept

    converted_weather_data = controller.convert_names_and_units(
        source_id, model_id, False, weather_data, fmt_args.units
    )

    lat_values = [float(x) for x in np.atleast_1d(converted_weather_data.coords["lat"].values)]
    lon_values = [float(x) for x in np.atleast_1d(converted_weather_data.coords["lon"].values)]
    new_coords = [(lat, lon) for lat, lon in zip(lat_values, lon_values)]

    response, optional_file_path = serializers.return_file_or_text_response(
        converted_weather_data, response_format, source_id, model_id, ret_args, new_coords
    )
    cleanup_tasks.add_task(remove_file, optional_file_path)
    logger.info(f"WeatherRequest({starting_time}) data preparation finished.")
    return response


# @weather_provider_api.get("/weeralarm")
@v2_router.get("/alarms/knmi", tags=["alerts"])
async def get_alarm() -> list[tuple[str, str]]:  # pragma: no cover
    """Fetch the WeatherAlarm status for all the provinces from KNMI Weer Alarm and returns the results.

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
    accept: ResponseFormat = Depends(header_accept_type),
) -> Response:  # pragma: no cover
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

    response, optional_file_path = serializers.return_file_or_text_response(
        converted_weather_data, response_format, source_id, model_id, ret_args, coords
    )
    cleanup_tasks.add_task(remove_file, optional_file_path)
    logger.info(f"WeatherRequest({starting_time}) data preparation finished.")
    return response
