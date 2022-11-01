#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

from fastapi import FastAPI

from weather_provider_api.app_config import get_setting
from weather_provider_api.routers.weather.api_view_v2 import app as weather_router

app = FastAPI(title="Weather API", root_path="/api/v2", version=get_setting("APP_V2_VERSION"))

app.include_router(weather_router, prefix="/weather")
