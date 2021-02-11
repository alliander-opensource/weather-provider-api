#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

from app.core.initializers.error_handling import initialize_error_handling
from fastapi import FastAPI


def mount_api_version(base_app: FastAPI, versioned_app):
    """Mounts a versioned API application.

    This method helps to expose an API version to the main application.
    Additionally, it ensures Alliander core API endpoints are set. The latter
    are obligatory and may not be removed or bypassed.

    Args:
        base_app: main FastAPI application
        versioned_app: versioned FastAPI application
    """
    from app.core.views import router

    initialize_error_handling(versioned_app)
    versioned_app.include_router(router, prefix="/core")
    base_app.mount(versioned_app.root_path, versioned_app)
