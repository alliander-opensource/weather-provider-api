#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from typing import Annotated

import accept_types  # type: ignore
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Response

from weather_provider_api.routers.weather.api_models import (
    ResponseFormat,
    WeatherContentRequestQuery,
    WeatherFormattingRequestQuery,
    WeatherModel,
    WeatherSource,
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

app = APIRouter()

controller = WeatherController()


def header_accept_type(accept: str = Header(None)) -> str:
    """Match the Accept header to the best fitting MIME type for the output format, based on the supported types."""
    best_match_or_none = accept_types.get_best_match(accept, result_mime_types)  # type: ignore
    return result_mime_types[best_match_or_none]  # type: ignore


# @weather_provider_api.get("/sources", response_model=List[WeatherSource], tags=["sync", "async"])
@app.get("/sources", response_model=list[WeatherSource], tags=["sync"])
async def get_sources() -> list[WeatherSourceBase]:  # pragma: no cover
    """List all the sources known by the controller."""
    return controller.get_sources()


# @weather_provider_api.get("/sources/{source_id}", response_model=WeatherSource, tags=["sync", "async"])
@app.get("/sources/{source_id}", response_model=WeatherSource, tags=["sync"])
async def get_source(source_id: str) -> WeatherSourceBase | None:  # pragma: no cover
    """Get a specific source by its ID."""
    source_id = source_id.lower()
    return controller.get_source(source_id)


@app.get("/sources/{source_id}/models", response_model=list[WeatherModel], tags=["sync"])
async def get_sync_models(source_id: str) -> list[WeatherModelBase]:  # pragma: no cover
    """List all the synchronous models supported by the selected source."""
    source_id = source_id.lower()
    return controller.get_models(source_id, fetch_async=False)


@app.get(
    "/sources/{source_id}/models/{model_id}",
    tags=["sync"],
    responses={404: {"description": "Not Found"}},
)
async def get_sync_weather(
    source_id: str,
    model_id: str,
    cleanup_tasks: BackgroundTasks,
    ret_args: Annotated[WeatherContentRequestQuery, Depends(get_weather_content_request_query)],
    fmt_args: Annotated[WeatherFormattingRequestQuery, Depends(get_weather_formatting_request_query)],
    accept: Annotated[ResponseFormat, Depends(header_accept_type)],
) -> Response:  # pragma: no cover
    """Gather and return weather data for a specific model and source, using the specified parameters.

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
        accept:     The best matching response MIME type based on the request's Accept header

    Returns:
        Returns a file in the requested output format, containing any weather data that matched the specifications from
        the WeatherContentRequestQuery.

    """
    source_id = source_id.lower()
    model_id = model_id.lower()
    coords: list[list[tuple[float, float]]] = controller.lat_lon_to_coords(ret_args.lat, ret_args.lon)

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

    new_coords = [
        (lat_val, lon_val)  # type: ignore
        for (lat_val, lon_val) in zip(
            converted_weather_data.coords["lat"].values,
            converted_weather_data.coords["lon"].values,
        )
    ]

    response, optional_file_path = serializers.return_file_or_text_response(
        unserialized_data=converted_weather_data,
        response_format=response_format,
        source_id=source_id,
        model_id=model_id,
        request=ret_args,
        coords=new_coords,
    )
    cleanup_tasks.add_task(remove_file, optional_file_path)

    return response


# @weather_provider_api.get("/weeralarm")
@app.get("/alarms/knmi", tags=["alerts"])
async def get_alarm() -> list[tuple[str, str]]:  # pragma: no cover
    """Fetch the WeatherAlarm status for all the provinces from KNMI Weer Alarm and return the results."""
    weather_alert = WeatherAlert()
    return weather_alert.get_alarm()
