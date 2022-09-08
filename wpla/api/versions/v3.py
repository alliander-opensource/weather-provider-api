#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
===================================
Version 3.x API Application Context
===================================

This module holds the application context for the version 3.x API part of the application.

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
