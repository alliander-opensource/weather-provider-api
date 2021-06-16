#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from fastapi import FastAPI

from weather_provider_api.app.routers.weather.api_view_v1 import app as weather_router

app = FastAPI(title="Weather API", root_path="/api/v1")

app.include_router(weather_router, prefix="/weather")
