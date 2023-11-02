#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" CORS support """

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from weather_provider_api.config import APP_CONFIG


def initialize_cors_middleware(app: FastAPI):
    """Initializes the CORS middleware.

    Enables CORS handling for the allowed origins set in the config setting `CORS_ALLOWED_ORIGINS`, a list of strings
     each corresponding to a host. The FastAPI CORSMiddleware is used to enable CORS handling.

    Args:
        app (FastAPI):  The FastAPI application to attach the CORS middleware to.

    Returns:
        Nothing. The application itself is updated.

    """
    origins = APP_CONFIG["components"]["cors_allowed_origins"]
    origins_regex = APP_CONFIG["components"]["cors_allowed_origins_regex"]

    if origins and len(origins) == 0:
        origins = None
    if origins_regex and len(origins_regex) == 0:
        origins_regex = None

    if origins and origins_regex:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            allow_origins_regex=origins_regex,
        )
        logger.info(f"Attached CORS middleware enabled for the following origins: {origins}, {origins_regex}")
    elif origins:
        app.add_middleware(
            CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
        )
        logger.info(f"Attached CORS middleware enabled for the following origins: {origins}")
    elif origins_regex:
        app.add_middleware(
            CORSMiddleware,
            allow_origins_regex=origins_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(f"Attached CORS middleware enabled for the following origins: {origins_regex}")
    else:
        logger.warning("CORS middleware enabled but no allowed origins are set.")
