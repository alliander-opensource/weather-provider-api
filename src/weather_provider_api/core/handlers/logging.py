#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import logging
import os
import sys

from loguru import logger

from weather_provider_api.configuration import API_CONFIGURATION
from weather_provider_api.core.handlers.logger_components.log_formats import LogFormats
from weather_provider_api.core.handlers.logger_components.logging_intercept_handler import LoggingInterceptHandler


def setup_included_project_logger():
    """Initializes the project logger with the settings from the configuration file."""
    __cleanup_existing_loggers()
    __replace_basic_logging_with_loguru()
    __setup_new_logger()
    __propagate_uvicorn_to_default_handler()


def __cleanup_existing_loggers():
    logger.remove()


def __replace_basic_logging_with_loguru():
    logging.basicConfig(handlers=[LoggingInterceptHandler()], level=0)


def __setup_new_logger():
    log_level = (
        os.environ.get("LOG_LEVEL") or API_CONFIGURATION.component_settings.project_logger.get("log_level", "info")
    ).upper()
    log_format = (
        os.environ.get("LOG_FORMAT")
        or API_CONFIGURATION.component_settings.project_logger.get("log_format", "plain").lower()
    )

    serialize = log_format == "json"
    log_format = LogFormats[log_format].value if log_format in LogFormats.__members__ else LogFormats.plain

    logger.add(sys.stdout, enqueue=False, level=log_level, format=log_format, serialize=serialize)
    logging.info("Logger initialized")


def __propagate_uvicorn_to_default_handler():
    for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(uvicorn_logger).handlers.clear()
        logging.getLogger(uvicorn_logger).propagate = True

    logging.info("Uvicorn loggers successfully propagated to default logger")
