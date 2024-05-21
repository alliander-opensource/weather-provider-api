#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import APIRouter
from starlette.requests import Request

v3_router = APIRouter()


@v3_router.get(
    "/info/list-sources",
    tags=["information"],
    response_model=dict,
    name="List Sources",
    description="Get a list of available sources for weather data.",
)
async def list_sources(request: Request):
    """Get sources for weather data."""
    return {"sources": ["source1", "source2"]}


@v3_router.get(
    "/info/list-models",
    tags=["information"],
    response_model=dict,
    name="List Models",
    description="Get a list of available models for weather data.",
)
async def list_models(request: Request, source: str):
    """Get models for weather data."""
    return {"models": ["model1", "model2"]}


@v3_router.get(
    "/info/model-info",
    tags=["information"],
    response_model=dict,
    name="Model Info",
    description="Get information about a specific model.",
)
async def model_info(request: Request, source: str, model: str):
    """Get information about a specific model."""
    return {"info": "info"}


@v3_router.get(
    "/request/weather-data",
    tags=["request"],
    response_model=dict,
    name="Weather Data",
    description="Request weather data.",
)
async def weather_data(request: Request, source: str, model: str, request_parameters: str):
    """Request weather data."""
    return {"data": "data"}


@v3_router.post(
    "/request/weather-data-en-masse",
    tags=["request"],
    response_model=dict,
    name="Weather Data en Masse",
    description="Request weather data for large quantities of locaties or time.",
)
async def weather_data_en_masse(request: Request, source: str, model: str, request_parameters: str):
    """Request weather data for large quantities of locaties or time."""
    return {"data": "data"}
