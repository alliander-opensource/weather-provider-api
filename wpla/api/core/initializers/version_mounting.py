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
    place to hook up these versioned API's.
"""

from fastapi import APIRouter, FastAPI

from wpla.api.core.initializers.error_handling import initialize_error_handling


def mount_api_version(base_app: FastAPI, versioned_app: FastAPI):
    """Function that adds the versioned API onto an existing app"""
    initialize_error_handling(versioned_app)  # Versioned hookup
    versioned_app.include_router(router=APIRouter(), prefix='/core')
    base_app.mount(versioned_app.root_path, versioned_app)
