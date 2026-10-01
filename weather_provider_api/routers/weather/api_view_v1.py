# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Response

from weather_provider_api.routers.weather.api_models import (
    ResponseFormat,
    WeatherContentRequestQuery,
    WeatherFormattingRequestQuery,
    WeatherModel,
    WeatherSource,
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

app = APIRouter(deprecated=True)

app.add_api_route("/sources", get_sources, response_model=list[WeatherSource], tags=["sync"])
app.add_api_route("/sources/{source_id}", get_source, response_model=WeatherSource, tags=["sync"])
app.add_api_route(
    "/sources/{source_id}/models",
    get_sync_models,
    response_model=list[WeatherModel],
    tags=["sync"],
)


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
    """Gather and return weather data for a specific model and source."""
    return await get_weather_response(
        source_id,
        model_id,
        cleanup_tasks,
        ret_args,
        fmt_args,
        accept,
        controller.lat_lon_to_coords(ret_args.lat, ret_args.lon),
    )


app.add_api_route("/alarms/knmi", get_alarm, tags=["alerts"])
