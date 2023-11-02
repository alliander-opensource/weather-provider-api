#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from fastapi import FastAPI

from weather_provider_api.config import APP_CONFIG, APP_SERVER
from weather_provider_api.routers.weather.api_view_v1 import app as weather_router

app = FastAPI(
    version=APP_CONFIG["api_v1"]["implementation"],
    title="Weather API (v1)",
    root_path="/api/v1",
    servers=[{"url": f"{APP_SERVER}/api/v1"}],
    description="The v1 endpoint interface for the Weather Provider API",
    contact={"name": APP_CONFIG["maintainer"]["name"], "email": APP_CONFIG["maintainer"]["email_address"]},
)

app.openapi_version = "3.0.2"

app.include_router(weather_router, prefix="/api/v1/weather")
app.openapi()
