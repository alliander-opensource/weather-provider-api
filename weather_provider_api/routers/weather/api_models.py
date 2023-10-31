#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, List

from fastapi import Query
from pydantic import Field
from starlette.responses import Response as StarletteResponse

from weather_provider_api.core.base_model import BaseModel

"""
    API request models, response models, and examples.
"""


# Note: while this can be done automatically, and for e.g. sources as well,
# I don't want new OpenAPI specs to be created when e.g. a source is added.


class OutputUnit(str, Enum):
    # Valid output unit sets
    si = "si"
    human = "human"
    original = "original"


class ResponseFormat(str, Enum):
    # Valid output file-formats
    netcdf4 = "netcdf4"
    netcdf3 = "netcdf3"
    json = "json"
    json_dataset = "json_dataset"
    csv = "csv"


class WeatherModel(BaseModel):
    id: str = Field(..., description="Model id")
    name: str = Field(..., description="Model name")
    version: str = Field("", description="Model version")
    url: str = Field("", description="Model URL")
    description: str = Field("", description="Model description")
    predictive: bool = Field(..., description="Predictions or measurements")
    async_model: bool = Field(..., description="Whether the model should be called asynchronously")
    time_step_size_minutes: int = Field(..., description="Time between each measurement or prediction")
    num_time_steps: int = Field(..., description="Number of data points in the result set")


class WeatherSource(BaseModel):
    id: str = Field(..., description="Source id")
    name: str = Field(..., description="Source name")
    url: str = Field(None, description="Source URL")
    models: List[WeatherModel] = Field(None, description="Synchronous models")
    async_models: List[WeatherModel] = Field(None, description="Asynchronous models")


@dataclass
class WeatherFormattingRequestQuery:
    units: OutputUnit = Query(OutputUnit.si, description="Unit of weather factors")
    response_format: ResponseFormat = Query(
        ResponseFormat.netcdf4,
        description="Response format (overrides mime-types from Accept HTTP header)",
    )


# Note: I'd love to combine the (almost) duplicate entries below, but the hybrid solutions don't work in FastAPI 0.30.
@dataclass
class WeatherContentRequestQuery:
    # TODO: Change Example value to current date base values
    begin: str = Query(None, description="From date and time", example="2019-01-01 00:00")
    end: str = Query(None, description="To date and time", example="2019-01-31 23:59")
    lat: float = Query(..., description="GPS Latitude or RD x-coordinate", example=52.10)
    lon: float = Query(..., description="GPS Longitude or RD y-coordinate", example=5.18)
    factors: List[str] = Query(None, description="Only return these weather factors (default: all factors)")


@dataclass
class WeatherContentRequestMultiLocationQuery:
    begin: str = Query(None, description="From date and time", example="2019-01-01 00:00")
    end: str = Query(None, description="To date and time", example="2019-01-31 23:59")
    locations: str = Query(
        None,
        description="Locations in either WGS84 (lat,lon) or RD (x,y) format, " "in parentheses, separated by a comma",
        example="(52.1, 5.18), (52.2, 5.22)",
    )
    factors: List[str] = Query(None, description="Only return these weather factors (default: all factors)")


class WeatherContentRequestBody(BaseModel):
    begin: str = Field(None, description="From date and time", example="2019-01-01 00:00")
    end: str = Field(None, description="To date and time", example="2019-01-31 23:59")
    lat: float = Field(..., description="GPS Latitude or RD x-coordinate", example=52.10)
    lon: float = Field(..., description="GPS Longitude or RD y-coordinate", example=5.18)
    factors: List[str] = Field(None, description="Only return these weather factors (default: all factors)")


class ScientificJSONResponse(StarletteResponse):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=True,
            indent=None,
            separators=(",", ":"),
            default=str,
            cls=FloatEncoder,
        ).encode("utf-8")


class FloatEncoder(json.JSONEncoder):
    INFINITY = float("inf")

    def iterencode(self, obj, **kwargs):
        if isinstance(obj, float):
            if math.isnan(obj):  # This checks for NaNs ;-)
                yield "null"
            elif obj == FloatEncoder.INFINITY:
                yield "Infinity"
            elif obj == -FloatEncoder.INFINITY:
                yield "-Infinity"
            else:
                yield format(obj, ".4f")
        elif isinstance(obj, dict):
            last_index = len(obj) - 1
            yield "{"
            i = 0
            for key, value in obj.items():
                yield '"' + key + '": '
                for chunk in FloatEncoder.iterencode(self, value):
                    yield chunk
                if i != last_index:
                    yield ", "
                i += 1
            yield "}"
        elif isinstance(obj, list):
            last_index = len(obj) - 1
            yield "["
            for i, o in enumerate(obj):
                for chunk in FloatEncoder.iterencode(self, o):
                    yield chunk
                if i != last_index:
                    yield ", "
            yield "]"
        else:
            for chunk in json.JSONEncoder.iterencode(self, obj):
                yield chunk


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
