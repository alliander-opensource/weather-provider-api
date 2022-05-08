#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""The logging initialisation module

This module holds the full configuration and initialisation for logging the entire API and its components. It only
needs to be hooked up to the FastAPI app in the proper way, and if you wish to include pre-launch data with this
configuration, it also needs to be started before the app configuration.

"""

import logging
import sys

from loguru import logger

from wpla.configuration import app_config


class InterceptHandler(logging.Handler):
    """A Log level converter between the default logger and the loguru levels"""
    loglevel_mapping = {
        50: "CRITICAL",
        40: "ERROR",
        30: "WARNING",
        20: "INFO",
        10: "DEBUG",
        0: "NOTSET",
    }

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def initialize_logging():
    """The logging initializer. The only place you need to look for log configuration."""
    logger.remove()  # Clean existing loggers
    log_format = (
        "<level>{level: <8}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
        " - <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )  # Set the loging format to use

    # Hook up the STDOUT logger:
    logger.add(
        sys.stdout,
        enqueue=True,
        backtrace=True,
        level=app_config.logging_level,
        format=log_format,
    )

    # Hook up the FILE Logger:  ---> Not currently in use
    """
    logger.add(
        str('filename.ext'),  # target file
        rotation='14 days',
        retention='1 months',
        enqueue=True,
        backtrace=True,
        level=app_config.logging_level,
        format=log_format
    )
    """

    # As uvicorn wants to use its own handlers, we find those if they already exist, and replace them with our own
    uvicorn_loggers = (
        logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("uvicorn.")
    )
    intercept_handler = InterceptHandler()
    for uvicorn_logger in uvicorn_loggers:
        uvicorn_logger.handlers = [intercept_handler]

    logging.basicConfig(handlers=[InterceptHandler()], level=0)
