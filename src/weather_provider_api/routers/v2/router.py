#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import APIRouter
from starlette.requests import Request

from weather_provider_api.core.handlers.rate_limiting import custom_rate_limiter

v2_router = APIRouter()


@v2_router.get("/sources", response_model=list[dict], tags=["sync"])
async def get_sources(request: Request):
    """List all sources."""
    return [{"source": "source1"}, {"source": "source2"}]


@v2_router.get("/sources/{source_id}", response_model=dict, tags=["sync"])
async def get_source(request: Request, source_id: str):
    """List a specific source and all of its models."""
    source_id = source_id.lower()
    return {"source": source_id, "models": ["model1", "model2"]}


@v2_router.get("/sources/{source_id}/models", response_model=list[dict], tags=["sync"])
async def get_sync_models(request: Request, source_id: str):
    """List all models for a specific source."""
    source_id = source_id.lower()
    return [{"model": "model1"}, {"model": "model2"}]


@v2_router.get("/sources/{source_id}/models/{model_id}", response_model=dict, tags=["sync"])
async def get_sync_weather(
    request: Request,
    source_id: str,
    model_id: str,
    ret_args: str,
    fmt_args: str,
):
    """Gathers and returns the weather data for a specific source and model."""
    return {"weather_data": "weather_data"}


# @weather_provider_api.get("/weeralarm")
@v2_router.get("/alarms/knmi", tags=["alerts"])
async def get_alarm():
    """Get the current weather alarm from the KNMI."""
    return {"alarm": "alarm"}


# Handler for requests with multiple locations:
@v2_router.get("/sources/{source_id}/models/{model_id}/multiple-locations/", tags=["sync"])
@custom_rate_limiter.limit("1/minute")
async def get_sync_weather_multi_loc(request: Request, source_id: str, model_id: str, ret_args: str, fmt_args: str):
    """Gathers and returns the weather data for multiple locations."""
    return {"weather_data": "weather_data"}
