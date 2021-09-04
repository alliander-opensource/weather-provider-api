#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from fastapi import FastAPI

from weather_provider_api.app.routers.api_view_v2 import app as weather_router
from weather_provider_api.app.core.config import Config

app = FastAPI(title="Weather Provider API - version 2", root_path="/api/v2",
              version=Config["app"]["endpoints"]["v2_version"])

app.include_router(weather_router, prefix="/weather")
