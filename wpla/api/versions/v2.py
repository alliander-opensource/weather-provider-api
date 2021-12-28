#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""
=============================
The WPLA API v2.x app context
=============================

This module creates an FastAPI app context for the 2.x API interface version of WPLA.
"""
from fastapi import FastAPI

from wpla.api.routers.api_view_v2 import app as weather_router

v2_api_version = 'v2_0.8'
v2_api_validation_date = '2022-12-31'

app = FastAPI(
    title="Weather Provider Libraries and API - v2",
    root_path="/api/v2",
    version=v2_api_version
)

app.include_router(weather_router, prefix="/weather")
