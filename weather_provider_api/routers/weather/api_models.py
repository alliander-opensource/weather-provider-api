#  SPDX-FileCopyrightText: 2019-2026 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import json
import math
from collections import defaultdict
from dataclasses import field
from datetime import UTC, date, datetime, time, timedelta
from enum import Enum
from typing import Any, List

from fastapi import Query
from pydantic import Field
from pydantic.dataclasses import dataclass
from starlette.responses import Response as StarletteResponse

from weather_provider_api.core.base_model import BaseModel

# Constants for repeated string literals
FROM_DATE_AND_TIME = "From date and time"
TO_DATE_AND_TIME = "To date and time"
FACTORS_DESCRIPTION = "Only return these weather factors (default: all factors)"


class OutputUnit(str, Enum):
    """Enumeration of valid output unit sets for weather data."""

    # Valid output unit sets
    si = "si"
    human = "human"
    original = "original"


class ResponseFormat(str, Enum):
    """Enumeration of valid output file-formats for weather data responses."""

    # Valid output file-formats
    netcdf4 = "netcdf4"
    netcdf3 = "netcdf3"
    json = "json"
    json_dataset = "json_dataset"
    csv = "csv"


def _yesterday_midnight():
    return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d 00:00")


def _yesterday_end():
    return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d 23:59")


class WeatherModel(BaseModel):
    """Model describing a weather model's metadata and configuration."""

    id: str = Field(..., description="Model id")
    name: str = Field(..., description="Model name")
    version: str = Field(default="", description="Model version")
    url: str = Field(default="", description="Model URL")
    description: str = Field(default="", description="Model description")
    predictive: bool = Field(..., description="Predictions or measurements")
    async_model: bool = Field(..., description="Whether the model should be called asynchronously")
    time_step_size_minutes: int = Field(..., description="Time between each measurement or prediction")
    num_time_steps: int = Field(..., description="Number of data points in the result set")


class WeatherSource(BaseModel):
    """Model describing a weather data source and its available models."""

    id: str = Field(..., description="Source id")
    name: str = Field(..., description="Source name")
    url: str | None = Field(default=None, description="Source URL")
    models: List[WeatherModel] | None = Field(default=None, description="Synchronous models")
    async_models: List[WeatherModel] | None = Field(default=None, description="Asynchronous models")



class WeatherFormattingRequestQuery(BaseModel):
    """Query parameters for formatting weather data responses."""
    units: OutputUnit = Field(
        default=OutputUnit.si,
        description="Unit of weather factors",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.netcdf4,
        description="Response format (overrides mime-types from Accept HTTP header)",
    )


# Note: I'd love to combine the (almost) duplicate entries below, but the hybrid solutions don't work in FastAPI 0.30.
class WeatherContentRequestQuery(BaseModel):
    """Request query model for synchronous weather data requests, containing all necessary parameters for data retrieval and formatting."""

    begin: str | None = Field(
        default=None,
        description=FROM_DATE_AND_TIME,
        examples=[_yesterday_midnight()],
    )
    end: str | None = Field(
        default=None,
        description=TO_DATE_AND_TIME,
        examples=[_yesterday_end()],
    )
    lat: float = Field(
        ...,
        description="GPS Latitude or RD x-coordinate",
        examples=[52.10],
    )
    lon: float = Field(
        ...,
        description="GPS Longitude or RD y-coordinate",
        examples=[5.18],
    )
    factors: list[str] | None = Field(
        default=None,
        description=FACTORS_DESCRIPTION,
    )


@dataclass
class WeatherContentRequestMultiLocationQuery:
    """Request query model for synchronous weather data requests with multiple locations, containing all necessary parameters for data retrieval and formatting."""

    begin: str = field(
        default_factory=lambda: Query(None, description=FROM_DATE_AND_TIME, examples=[_yesterday_midnight()])
    )
    end: str = field(default_factory=lambda: Query(None, description=TO_DATE_AND_TIME, examples=[_yesterday_end()]))
    locations: str = field(
        default_factory=lambda: Query(
            None,
            description="Locations in either WGS84 (lat,lon) or RD (x,y) format, in parentheses, separated by a comma",
            examples=["(52.1, 5.18), (52.2, 5.22)"],
        )
    )
    factors: list[str] | None = field(default_factory=lambda: Query(None, description=FACTORS_DESCRIPTION))


class WeatherContentRequestBody(BaseModel):
    """Request body model for asynchronous weather data requests, containing all necessary parameters for data retrieval and formatting."""

    begin: str | None = Field(..., description=FROM_DATE_AND_TIME, examples=[_yesterday_midnight()])
    end: str | None = Field(..., description=TO_DATE_AND_TIME, examples=[_yesterday_end()])
    lat: float = Field(..., description="GPS Latitude or RD x-coordinate", examples=[52.10])
    lon: float = Field(..., description="GPS Longitude or RD y-coordinate", examples=[5.18])
    factors: list[str] | None = Field(default=None, description=FACTORS_DESCRIPTION)


class ScientificJSONResponse(StarletteResponse):
    """Custom response class for returning scientific data in JSON format, with specific handling for float formatting and special float values."""

    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        """Render the content as JSON, ensuring that floats are formatted to a maximum of 4 decimal places and that NaN and Infinity values are handled appropriately."""
        # If the top-level value is a float, wrap it in a list so FloatEncoder.default is called
        return json.dumps(sanitize_for_json(content), allow_nan=True).encode("utf-8")


def sanitize_for_json(obj: Any) -> Any:
    """Sanitize values before json.dumps.

    - NaN -> None
    - +Infinity -> "Infinity"
    - -Infinity -> "-Infinity"
    - finite floats -> rounded to 4 decimals
    - dict/list/tuple/set values are sanitized recursively
    """
    if isinstance(obj, float):
        if math.isnan(obj):
            return None
        if math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        return round(obj, 4)

    if isinstance(obj, datetime):
        return obj.isoformat()

    if isinstance(obj, date):
        return obj.isoformat()

    if isinstance(obj, time):
        return obj.isoformat()

    if isinstance(obj, dict):
        return {
            key: sanitize_for_json(value)
            for key, value in obj.items()  # type: ignore
        }

    if isinstance(obj, list):
        return [sanitize_for_json(value) for value in obj]  # type: ignore

    if isinstance(obj, tuple):
        return tuple(sanitize_for_json(value) for value in obj)  # type: ignore

    if isinstance(obj, set):
        return [sanitize_for_json(value) for value in obj]  # type: ignore

    return obj


result_mime_types = defaultdict(
    lambda: ResponseFormat.netcdf4,
    {
        "application/netcdf": ResponseFormat.netcdf4,
        "application/netcdf4": ResponseFormat.netcdf4,
        "application/x-netcdf": ResponseFormat.netcdf4,
        "application/netcdf3": ResponseFormat.netcdf3,
        "application/x-netcdf3": ResponseFormat.netcdf3,
        "application/json": ResponseFormat.json,
        "application/json-dataset": ResponseFormat.json_dataset,
        "text/csv": ResponseFormat.csv,
    },
)


# Dependency function to build WeatherContentRequestQuery from query params
def get_weather_content_request_query(
    begin: str = Query(None, description=FROM_DATE_AND_TIME, examples=[_yesterday_midnight()]),
    end: str = Query(None, description=TO_DATE_AND_TIME, examples=[_yesterday_end()]),
    lat: float = Query(..., description="GPS Latitude or RD x-coordinate", examples=[52.10]),
    lon: float = Query(..., description="GPS Longitude or RD y-coordinate", examples=[5.18]),
    factors: list[str] | None = Query(None, description=FACTORS_DESCRIPTION),
) -> WeatherContentRequestQuery:
    return WeatherContentRequestQuery(
        begin=begin, end=end, lat=lat, lon=lon, factors=factors
    )


# Dependency function to build WeatherFormattingRequestQuery from query params
def get_weather_formatting_request_query(
    units: OutputUnit = Query(OutputUnit.si, description="Unit of weather factors"),
    response_format: ResponseFormat = Query(
        ResponseFormat.netcdf4,
        description="Response format (overrides mime-types from Accept HTTP header)",
    ),
) -> "WeatherFormattingRequestQuery":
    return WeatherFormattingRequestQuery(units=units, response_format=response_format)
