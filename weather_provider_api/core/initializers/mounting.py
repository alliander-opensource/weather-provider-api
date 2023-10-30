#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" (sub)-API Mounting

This module handles the mounting of sub-API's onto a main API.
"""

from fastapi import FastAPI
from loguru import logger

from weather_provider_api.core.initializers.exception_handling import (
    initialize_exception_handler,
)


def mount_api_version(base_application: FastAPI, api_to_mount: FastAPI):
    """The method that mounts a FastAPI object as a child into another.

    Args:
        base_application:   The FastAPI application to be used as the parent application.
        api_to_mount:       The FastAPI application to be used as the child application
    Returns:
        Nothing. The parent object itself is updated after this method.

    Notes:
        This implementation assumes that the child application at least has a [title] and [root_path] set, and that the
         parent application at least has a title set.
    """
    initialize_exception_handler(api_to_mount)  # Hookup the exception handler to the new sub-API
    base_application.mount(api_to_mount.root_path, api_to_mount)
    logger.info(f"Mounted API [{api_to_mount.title}] to [{base_application.title}] at: {api_to_mount.root_path}")
