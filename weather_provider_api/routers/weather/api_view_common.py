# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from typing import Annotated

import accept_types  # type: ignore
import numpy as np
from fastapi import BackgroundTasks, Depends, Header, HTTPException, Response

from weather_provider_api.routers.weather.api_models import (
    ResponseFormat,
    WeatherContentRequestMultiLocationQuery,
    WeatherContentRequestQuery,
    WeatherFormattingRequestQuery,
    get_weather_content_request_query,
    get_weather_formatting_request_query,
    result_mime_types,
)
from weather_provider_api.routers.weather.base_models.model import WeatherModelBase
from weather_provider_api.routers.weather.base_models.source import WeatherSourceBase
from weather_provider_api.routers.weather.controller import WeatherController
from weather_provider_api.routers.weather.sources.weather_alert.weather_alert import (
    WeatherAlert,
)
from weather_provider_api.routers.weather.utils import serializers
from weather_provider_api.routers.weather.utils.date_helpers import parse_datetime
from weather_provider_api.routers.weather.utils.file_helpers import remove_file

controller = WeatherController()


def header_accept_type(accept: str = Header(None)) -> ResponseFormat:
    """Match the Accept header to the best fitting supported response format.

    Args:
        accept (str): HTTP Accept header value.

    Returns:
        ResponseFormat: Best matching supported response format.
    """
    best_match = str(accept_types.get_best_match(accept, result_mime_types))  # type: ignore
    return result_mime_types[best_match]


async def get_sources() -> list[WeatherSourceBase]:  # pragma: no cover
    """List all the sources known by the controller."""
    return controller.get_sources()


async def get_source(source_id: str) -> WeatherSourceBase | None:  # pragma: no cover
    """Get a specific source by its ID."""
    return controller.get_source(source_id.lower())


async def get_sync_models(source_id: str) -> list[WeatherModelBase]:  # pragma: no cover
    """List all synchronous models supported by the selected source."""
    return controller.get_models(source_id.lower(), fetch_async=False)


async def get_alarm() -> list[tuple[str, str]]:  # pragma: no cover
    """Fetch the current weather alarm status for all provinces."""
    return WeatherAlert().get_alarm()


async def get_weather_response(
    source_id: str,
    model_id: str,
    cleanup_tasks: BackgroundTasks,
    ret_args: Annotated[
        WeatherContentRequestQuery | WeatherContentRequestMultiLocationQuery,
        Depends(get_weather_content_request_query),
    ],
    fmt_args: Annotated[WeatherFormattingRequestQuery, Depends(get_weather_formatting_request_query)],
    accept: Annotated[ResponseFormat, Depends(header_accept_type)],
    coords: list[list[tuple[float, float]]],
    response_coords: list[tuple[float, float]] | None = None,
) -> Response:
    """Fetch, format, and serialize weather data for an API request.

    Args:
        source_id (str): Identifier of the weather data source.
        model_id (str): Identifier of the weather model.
        cleanup_tasks (BackgroundTasks): Tasks used to remove temporary response files.
        ret_args (WeatherContentRequestQuery | WeatherContentRequestMultiLocationQuery):
            Weather request parameters.
        fmt_args (WeatherFormattingRequestQuery): Response units and optional format override.
        accept (ResponseFormat): Response format selected from the HTTP Accept header.
        coords (list[list[tuple[float, float]]]): Requested polygon coordinates.
        response_coords (list[tuple[float, float]] | None): Coordinates to include in point responses.

    Returns:
        Response: Serialized weather data response.

    Raises:
        HTTPException: If the requested data is unavailable or the repository file is missing.
    """
    source_id = source_id.lower()
    model_id = model_id.lower()

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

    if response_coords is None:
        lat_values = [float(value) for value in np.atleast_1d(converted_weather_data.coords["lat"].values)]
        lon_values = [float(value) for value in np.atleast_1d(converted_weather_data.coords["lon"].values)]
        response_coords = list(zip(lat_values, lon_values, strict=True))

    response, optional_file_path = serializers.return_file_or_text_response(
        converted_weather_data,
        response_format,
        source_id,
        model_id,
        ret_args,
        response_coords,
    )
    cleanup_tasks.add_task(remove_file, optional_file_path)
    return response
