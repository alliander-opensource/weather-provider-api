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

from wpla.api.routers.core_views import app as core_router
from wpla.configuration import app_config

app = FastAPI(
    title="WPLA - Core", root_path="/core", version=app_config.version
)

app.include_router(core_router)
