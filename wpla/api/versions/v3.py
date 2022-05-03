#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
=============================
The WPLA API v3.x app context
=============================
This module creates an FastAPI app context for the 3.x API interface version of WPLA.
"""
from fastapi import FastAPI

from wpla.api.routers.api_view_v3 import app as weather_router
from wpla.configuration import app_config

app = FastAPI(
    title="WPLA - API Interface v3",
    root_path="/api/v3",
    version=app_config.api_versions["v3"]["api_version"],
)

app.include_router(weather_router, prefix="/weather")
