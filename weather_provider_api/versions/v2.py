#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from fastapi import FastAPI

from weather_provider_api.config import APP_CONFIG, APP_SERVER
from weather_provider_api.routers.weather.api_view_v2 import v2_router

app = FastAPI(
    version=APP_CONFIG["api_v2"]["implementation"],
    title="Weather API (v2)",
    root_path="/api/v2",
    servers=[{"url": f"{APP_SERVER}/api/v2"}],
    description="The v2 endpoint interface for the Weather Provider API",
    contact={"name": APP_CONFIG["maintainer"]["name"], "email": APP_CONFIG["maintainer"]["email_address"]},
)

app.openapi_version = "3.0.2"

app.include_router(v2_router, prefix="/weather")
app.openapi()
