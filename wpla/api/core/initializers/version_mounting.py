#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
from fastapi import APIRouter, FastAPI

from wpla.api.core.initializers.error_handling import initialize_error_handling

"""API Version Mounting

This module mounts a supplied versioned version of the API with its own router into a supplied base app. The base app
should ideally only be a container for these types of versioned apps.   
"""


def mount_api_version(base_app: FastAPI, versioned_app: FastAPI):
    initialize_error_handling(versioned_app)  # Versioned hookup
    versioned_app.include_router(router=APIRouter(), prefix='/core')
    base_app.mount(versioned_app.root_path, versioned_app)

