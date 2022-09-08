#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
============================
Core API Application Context
============================

This module holds the application context for the core API part of the application.

"""
from fastapi import FastAPI

from wpla.api.routers.core_views import app as core_router
from wpla.configuration import app_config

app = FastAPI(
    title="WPLA - Core", root_path="/core", version=app_config.version
)

app.include_router(core_router)
