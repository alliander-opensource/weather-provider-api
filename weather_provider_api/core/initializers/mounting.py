# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""(sub)-API Mounting.

This module handles the mounting of sub-API's onto a main API.
"""

from fastapi import FastAPI
from loguru import logger

from weather_provider_api.core.initializers.exception_handling import (
    initialize_exception_handler,
)
from weather_provider_api.core.initializers.rate_limiter import initialize_rate_limiter


def mount_api_version(base_application: FastAPI, api_to_mount: FastAPI, mount_path: str) -> None:
    """The method that mounts a FastAPI object as a child into another.

    Args:
        base_application:   The FastAPI application to be used as the parent application.
        api_to_mount:       The FastAPI application to be used as the child application
        mount_path:         The path prefix where the child API should be mounted.

    Returns:
        Nothing. The parent object itself is updated after this method.

    Notes:
        This implementation assumes that both applications have a title set.
    """
    initialize_exception_handler(api_to_mount)  # Hookup the exception handler to the new sub-API
    initialize_rate_limiter(api_to_mount)
    base_application.mount(mount_path, api_to_mount)
    logger.info(f"Mounted API [{api_to_mount.title}] to [{base_application.title}] at: {mount_path}")
