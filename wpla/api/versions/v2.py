#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from fastapi import FastAPI

from wpla.configuration import Config
from wpla.api.routers.api_view_v2 import app as weather_router

"""The Version 2.x WPLA API router hookup

This module creates an FastAPI app context for the 2.x API interface version of WPLA.
"""

app = FastAPI(
    title="Weather Provider Libraries and API - v2",
    root_path="/api/v2",
    version=Config['app']['active_api_versions']['v2_version']
)

app.include_router(weather_router, prefix="/weather")
