#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from weather_provider_api.configuration import API_CONFIGURATION


def attach_cors_handler(application: FastAPI):
    """Attach a CORS handler to the FastAPI application."""
    allowed_origins = API_CONFIGURATION.component_settings.cors.get("allowed_origins", [])
    allowed_origins_regex = API_CONFIGURATION.component_settings.cors.get("allowed_origins_regex", [])

    if len(allowed_origins_regex) > 0:
        logging.debug(f"CORS middleware enabled for origins regex: {allowed_origins_regex}")
        # noinspection PyTypeChecker
        application.add_middleware(
            CORSMiddleware,
            allow_origins_regex=allowed_origins_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    elif len(allowed_origins) > 0:
        logging.debug(f"CORS middleware enabled for origins: {allowed_origins}")
        # noinspection PyTypeChecker
        application.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        logging.debug("CORS middleware disabled")
