#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""
====================
API Version Mounting
====================

This module allows for the mounting of several sub-applications onto a main application.

In practice this means that we mount the actual API component versions onto the main application to allow for multiple
 versions being accessible simultaneously.

Notes:
    While the main application can also contain API elements itself, for greater clarity, it is best if the main
     application only serves as a mounting point for middleware, logging, exception handling and mounting the actual
     API elements.

"""

from fastapi import FastAPI
from loguru import logger

from wpla.api.core.initializers.exception_handling import (
    initialize_error_handling,
)
from wpla.api.routers.core_views import app as base_router

def mount_api_version(base_app: FastAPI, sub_app: FastAPI):
    """ This function mounts a sub-application to a base main application

    Args:
        base_app:       The base main application to use as a mounting point
        versioned_app:  The sub-application to mount

    """
    logger.info(f"Hooking up [{sub_app.title}] to [{base_app.title}]")
    initialize_error_handling(sub_app)  # Versioned error handling hookup
    sub_app.include_router(base_router, prefix="/core")
    base_app.mount(sub_app.root_path, sub_app)
