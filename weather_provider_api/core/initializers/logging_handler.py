#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2023 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

""" Logging Handler

This module initializes the logging intercept handler, which intercepts other logging methods and translates them into
 the intended loguru logging format.
"""

import logging
import sys
from pathlib import Path
from tempfile import gettempdir

from loguru import logger

from weather_provider_api.config import APP_DEBUGGING, APP_CONFIG, APP_LOG_LEVEL


class LoggingInterceptHandler(logging.Handler):
    """A class with the purpose of intercepting all log messages, and forwarding it to our own custom logging system.

    Notes:
        For our custom logging, we use Loguru.

    """

    log_level_map = {  # A level-translation map to translate numerical logging levels to string-based levels.
        50: "CRITICAL",
        40: "ERROR",
        30: "WARNING",
        20: "INFO",
        10: "DEBUG",
        0: "NOTSET",
    }

    def emit(self, record: logging.LogRecord) -> None:
        """Emission method that intercepts the original logging message using Python's base logging system and
         re-formats it (if needed) to match Loguru systems.

        Args:
            record: The original logging LogRecord object that holds a record to be converted.

        Returns:
            Nothing. We bind the converted message directly to de Loguru logger for processing.

        """
        # Set the proper level by name if possible, otherwise by using the translation map 'log_level_map'
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.log_level_map[record.levelno]

        # Set the proper log depth and frame to use
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Log the message as intended by writing the converted data to the proper log area.
        log = logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def initialize_logging():
    """The method that initializes and sets our custom logging system as the default, and reroutes other logging
     systems to use our system instead.
    Returns:
        Nothing. The logging system itself is overwritten.
    """
    logger.remove()  # Remove any existing default loggers from Loguru

    # Log formats:
    #  - [Elastic]: Holds the official format set as the Chapter standard by Data & Analytics.
    #  - [Develop]: Holds a more elaborate and colorful version of the log, good for debugging and development.
    log_format_elastic = "{level} [UTC {time:YYYY-MM-DD HH:mm:ss:SSS!UTC}] {message}"
    log_format_develop = (
        "<level>[{level: <8}]</level>"
        "<green>[{time:YYYY-MM-DD HH:mm:ss:SSS!UTC} UTC]</green> "
        "<cyan><i>{name}</i></cyan>|<blue><b>{function}</b></blue>: <level>{message}</level>"
    )

    log_format = log_format_develop if APP_DEBUGGING else log_format_elastic

    # Hook up the stdout logger if configured
    if APP_CONFIG["logging"]["use_stdout_logger"]:
        logger.add(
            sys.stdout,
            enqueue=False,
            backtrace=False,
            level=APP_LOG_LEVEL,
            format=log_format,
            diagnose=False,
        )

    # Hook up the file loggers if configured
    if APP_CONFIG["logging"]["use_file_loggers"]:
        # Determine log folder to use
        if Path(APP_CONFIG["logging"]["file_logger_folder"]).parent.exists():
            log_folder = Path(APP_CONFIG["logging"]["file_logger_folder"])
        else:
            log_folder = Path(gettempdir()).joinpath("logs")
        log_folder.mkdir(exist_ok=True)

        # Debug
        logger.add(
            log_folder.joinpath("debug.log"),
            enqueue=True,
            filter=lambda record: record["level"].name == "DEBUG",
            format=log_format,
        )
        # Info
        logger.add(
            log_folder.joinpath("info.log"),
            enqueue=True,
            filter=lambda record: record["level"].name == "INFO",
            format=log_format,
        )
        # Error
        logger.add(
            log_folder.joinpath("error.log"),
            enqueue=True,
            filter=lambda record: record["level"].name == "ERROR",
            format=log_format,
        )
        # Regular log
        logger.add(
            log_folder.joinpath("memo.log"),
            level=APP_LOG_LEVEL,
            format=log_format,
        )

    # Because Uvicorn already uses its own logger, we'll also need to replace those:
    existing_uvicorn_loggers = (
        logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("uvicorn.")
    )
    for uvicorn_logger in existing_uvicorn_loggers:
        uvicorn_logger.handlers = [LoggingInterceptHandler()]

    # Finally, we hook up the LoggingInterceptHandler as the default handler
    logging.basicConfig(handlers=[LoggingInterceptHandler()], level=0)
