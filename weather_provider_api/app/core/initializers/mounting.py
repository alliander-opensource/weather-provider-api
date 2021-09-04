#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from fastapi import FastAPI

from weather_provider_api.app.core.initializers.error_handling import initialize_error_handling
from weather_provider_api.app.core.initializers.validation import initialize_validation_api_version


def mount_api_version(base_app: FastAPI, versioned_app):
    """This function mounts a versioned API application.

    This method helps mounting an API version to the main application. Additionally, it also ensures certain core API
    endpoints are set.

    Args:
        base_app:       The main FastAPI application to mount within
        versioned_app:  The versioned FastAPI application to mount

    """
    from weather_provider_api.app.core.views import router

    initialize_error_handling(versioned_app)
    initialize_validation_api_version(versioned_app)
    versioned_app.include_router(router, prefix="/core")
    base_app.mount(versioned_app.root_path, versioned_app)
