#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
####################
API Version Mounting
####################
This module grafts a supplied output-version of the WPLA API onto the (supplied) base app.
Note:
    This base application should only serve as a mounting point for middleware, loggers and error handlers, and as the
    place to hook up these versioned APIs.
"""

from fastapi import FastAPI
from loguru import logger

from wpla.api.core.initializers.exception_handling import (
    initialize_error_handling,
)
from wpla.api.routers.core_views import app as base_router


def mount_api_version(base_app: FastAPI, versioned_app: FastAPI):
    """Function that adds the versioned API onto an existing app"""
    logger.info(f"Hooking up [{versioned_app.title}] to [{base_app.title}]")
    initialize_error_handling(versioned_app)  # Versioned error handling hookup
    versioned_app.include_router(base_router, prefix="/core")
    base_app.mount(versioned_app.root_path, versioned_app)
