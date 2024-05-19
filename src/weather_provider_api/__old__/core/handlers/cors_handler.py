#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from weather_provider_api.core.handlers.configuration_handler import WP_API_CONFIG


def install_cors_handler(app: FastAPI):
    """Install a CORS Handler into the FastAPI application if needed.

    This function installs a CORS handler into the FastAPI application if the configuration settings
    `components.cors_allowed_origins` or `components.cors_allowed_origins_regex` are set.

    Args:
        app (FastAPI):
            The FastAPI application to install the CORS handler into.

    """
    allowed_origins = WP_API_CONFIG["components"].get("cors_allowed_origins", [])
    allowed_origins_regex = WP_API_CONFIG["components"].get("cors_allowed_origins_regex", [])

    if len(allowed_origins_regex) > 0:
        logger.info(f"CORS middleware enabled for origins regex: {allowed_origins_regex}")
        app.add_middleware(
            CORSMiddleware,
            allow_origins_regex=allowed_origins_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    elif len(allowed_origins) > 0:
        logger.info(f"CORS middleware enabled for origins: {allowed_origins}")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        logger.info("CORS middleware disabled")
