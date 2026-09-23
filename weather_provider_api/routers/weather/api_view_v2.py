# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from loguru import logger

from weather_provider_api.core.initializers.rate_limiter import API_RATE_LIMITER
from weather_provider_api.routers.weather.api_models import (
    ResponseFormat,
    ScientificJSONResponse,
    WeatherContentRequestMultiLocationQuery,
    WeatherContentRequestQuery,
    WeatherFormattingRequestQuery,
    WeatherModel,
    WeatherSource,
    get_weather_content_request_multi_location_query,
    get_weather_content_request_query,
    get_weather_formatting_request_query,
)
from weather_provider_api.routers.weather.api_view_common import (
    controller,
    get_alarm,
    get_source,
    get_sources,
    get_sync_models,
    get_weather_response,
    header_accept_type,
)

v2_router = APIRouter()

# @weather_provider_api.get("/sources", response_model=List[WeatherSource], tags=["sync", "async"])
v2_router.add_api_route("/sources", get_sources, response_model=list[WeatherSource], tags=["sync"])


# @weather_provider_api.get("/sources/{source_id}", response_model=WeatherSource, tags=["sync", "async"])
v2_router.add_api_route("/sources/{source_id}", get_source, response_model=WeatherSource, tags=["sync"])


v2_router.add_api_route(
    "/sources/{source_id}/models",
    get_sync_models,
    response_model=list[WeatherModel],
    tags=["sync"],
)


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

    This data is then formatted as the requested output format (output unit system and file format) before returning
    the requested data.

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
    coords = controller.lat_lon_to_coords(ret_args.lat, ret_args.lon)
    response = await get_weather_response(
        source_id,
        model_id,
        cleanup_tasks,
        ret_args,
        fmt_args,
        accept,
        coords,
    )
    logger.info(f"WeatherRequest({starting_time}) data preparation finished.")
    return response


# @weather_provider_api.get("/weeralarm")
v2_router.add_api_route("/alarms/knmi", get_alarm, tags=["alerts"])


# Handler for requests with multiple locations:
@v2_router.get(
    "/sources/{source_id}/models/{model_id}/multiple-locations/",
    tags=["sync"],
    responses={
        200: {"description": "Successful response with the requested weather data."},
        404: {"description": "No data was found for the given period or file not found."},
        422: {"description": "Invalid or missing query parameters."},
    },
)
@API_RATE_LIMITER.limit("5/minute")  # type: ignore
async def get_sync_weather_multi_loc(
    request: Request,
    source_id: str,
    model_id: str,
    cleanup_tasks: BackgroundTasks,
    ret_args: Annotated[
        WeatherContentRequestMultiLocationQuery,
        Depends(get_weather_content_request_multi_location_query),
    ],
    fmt_args: Annotated[WeatherFormattingRequestQuery, Depends(get_weather_formatting_request_query)],
    accept: Annotated[ResponseFormat, Depends(header_accept_type)],
) -> Response:  # pragma: no cover
    """Request weather data for a specific Model using the given settings."""
    starting_time = datetime.now(UTC)
    logger.info(f"WeatherRequest({starting_time}): {request.url}")

    coords = controller.str_to_coords(ret_args.locations)
    response = await get_weather_response(
        source_id,
        model_id,
        cleanup_tasks,
        ret_args,
        fmt_args,
        accept,
        coords,
        [coord[0] for coord in coords],
    )
    logger.info(f"WeatherRequest({starting_time}) data preparation finished.")
    return response
