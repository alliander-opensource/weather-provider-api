#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import FastAPI
from loguru import logger

from weather_provider_api.core.handlers.exception_handler import install_exception_handler


def mount_fastapi_sub_app_to_app(base_application: FastAPI, sub_application: FastAPI):
    """Mount a FastAPI sub-application into a base application."""
    # First we make sure the custom Exception Handler is mounted onto the sub-application
    install_exception_handler(sub_application)

    # Determine where to mount the sub-application and what all the application names are:
    sub_application_title = sub_application.title if hasattr(sub_application, "title") else "Unknown"
    base_application_title = base_application.title if hasattr(base_application, "title") else "WP API"
    mounting_path = sub_application.root_path if hasattr(sub_application, "root_path") else f"/{sub_application_title}/"

    # Then we mount the sub-application onto the base application
    logger.info(
        f"WP API - Mounting sub-application [{sub_application_title}] to [{base_application_title}] at: "
        f"{mounting_path}"
    )
    base_application.mount(mounting_path, sub_application)
