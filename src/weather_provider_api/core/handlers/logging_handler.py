#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import logging
import sys

from fastapi import FastAPI
from loguru import logger

from weather_provider_api.core.handlers.configuration_handler import (
    WP_API_CONFIG,
    WP_API_ENV_VARS,
)

_LOG_FORMAT_SERVERLOG = "[{level}][UTC {time:YYYY-MM-DD HH:mm:ss:SSS!UTC}]: {message}"
_LOG_FORMAT_EXTENDED = (
    "<level>[{level: <8}]</level>"
    "<green>[{time:YYYY-MM-DD HH:mm:ss:SSS!UTC} UTC]</green>"
    "<yellow>[{name: <64}]</yellow>"
    "<blue><b>[{function: <36}]</b></blue>: "
    "<level>{message}</level>"
)
_LOG_FORMAT_SIMPLIFIED = (
    "<level>[{level: <8}]</level>"
    "<green>[{time:YYYY-MM-DD HH:mm:ss:SSS!UTC} UTC]</green>: "
    "<level>{message}</level>"
)
_LOG_FORMAT_FILES = "[{level}][UTC {time:YYYY-MM-DD HH:mm:ss:SSS!UTC}][{name} {function}]: {message}"


class LoggingInterceptHandler(logging.Handler):
    """A class that intercepts all log messages and forwards them to the customized Loguru logging system."""

    # A level-translation map to translate the numerical logging levels used by certain other logging systems.
    LOG_LEVEL_MAP = {
        50: "CRITICAL",
        40: "ERROR",
        30: "WARNING",
        20: "INFO",
        10: "DEBUG",
        0: "NOTSET",
    }

    def emit(self, record: logging.LogRecord):
        """Intercept the original logging messages and repurpose them for the custom Loguru logging system.

        Notes:
            To properly repurpose the original logging messages, this method will obtain any original logging
            record, and emit it itself using the Loguru logging system.

        Args:
            record (logging.LogRecord):
                The original logging record to be intercepted.

        """
        # First we try to set the proper logging level. If the level is not found by name, we use the translation map.
        try:
            record_level = logger.level(record.levelname).name
        except AttributeError:
            record_level = self.LOG_LEVEL_MAP[record.levelno]

        # Establish the log depth to use for the log message via the current frame within the original logging system.
        frame, depth = logging.currentframe(), 2  # The base depth level is 2

        # We keep moving a frame back from the logging module until we leave it, meaning we're no longer in a logging
        # layer and have reached the full depth of the original log message.
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Log the message as intended by writing the converted data to the proper logger.
        log = logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(record_level, "WP API - " + record.getMessage())


def install_logging_handler(app: FastAPI):
    """Install the logging handler to intercept all log messages and forward them to our custom logging system.

    Args:
        app: The FastAPI application instance to install the logging handler on.

    Returns:
        Nothing. The logging handler is installed on the FastAPI application instance.

    """
    logger.info("WP API - init - Attaching logging handler")
    app.add_event_handler("startup", initialize_logging)


def initialize_logging():
    """(Re-)initialize the logging system to use Loguru as the default logger."""
    # Remove any pre-existing Loguru loggers
    logger.remove()

    # Hook up any existing uvicorn related loggers to Loguru as well
    attach_uvicorn_loggers()

    # Add STD-OUT logging if requested
    if WP_API_CONFIG["logging"].get("use_stdout_logger", True):
        add_stdout_logger()

    # Add file loggers if requested
    if WP_API_CONFIG["logging"].get("use_file_loggers", False):
        add_file_loggers()

    # Setup the replacement LoggingInterceptHandler as the default logging handler
    logging.basicConfig(handlers=[LoggingInterceptHandler()], level=0)


def attach_uvicorn_loggers():
    """Attach any existing Uvicorn loggers to the Loguru logger."""
    existing_uvicorn_loggers = (
        logging.getLogger(name=name)
        for name in logging.root.manager.loggerDict
        if name.startswith("uvicorn.") or name.startswith("gunicorn.")
    )
    for existing_logger in existing_uvicorn_loggers:
        existing_logger.handlers = [LoggingInterceptHandler()]


def add_stdout_logger():
    """Add a STDOUT logger to Loguru.

    The standard server logging format is used unless the environment variable is set to EXTENDED.

    """
    _logging_format_from_env = WP_API_ENV_VARS.get("LOGGING_FORMAT", "SERVERLOG")

    logging_format = _LOG_FORMAT_SERVERLOG

    if _logging_format_from_env == "EXTENDED":
        logging_format = _LOG_FORMAT_EXTENDED
    elif _logging_format_from_env == "SIMPLIFIED":
        logging_format = _LOG_FORMAT_SIMPLIFIED

    logger.add(
        sys.stdout,
        enqueue=False,
        level=WP_API_CONFIG["logging"]["log_level"],
        format=logging_format,
    )


def add_file_loggers():
    """Add file loggers to Loguru."""
    log_storage_folder = WP_API_ENV_VARS.get("LOGGING_FOLDER", "/tmp/wpas_logs")

    logger.add(
        log_storage_folder.joinpath("debug.log"),
        enqueue=True,
        filter=lambda record: record["level"].name == "DEBUG",
        format=_LOG_FORMAT_FILES,
    )
    logger.add(
        log_storage_folder.joinpath("info.log"),
        enqueue=True,
        filter=lambda record: record["level"].name == "INFO",
        format=_LOG_FORMAT_FILES,
    )
    logger.add(
        log_storage_folder.joinpath("error.log"),
        enqueue=True,
        filter=lambda record: record["level"].name == "ERROR",
        format=_LOG_FORMAT_FILES,
    )
    logger.add(
        log_storage_folder.joinpath("memo.log"),
        level=WP_API_CONFIG["logging"]["log_level"],
        format=_LOG_FORMAT_FILES,
    )
