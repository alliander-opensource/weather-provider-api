#!/usr/bin/env python

#  -------------------------------------------------------
#  SPDX-FileCopyrightText: 2019-2024 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0
#  -------------------------------------------------------

import logging
from types import FrameType

from loguru import logger


class LoggingInterceptHandler(logging.Handler):
    """Intercept the original logging messages and repurpose them for the custom Loguru logging system."""

    LOG_LEVEL_MAPPING = {50: "CRITICAL", 40: "ERROR", 30: "WARNING", 20: "INFO", 10: "DEBUG", 0: "NOTSET"}

    def emit(self, record: logging.LogRecord):
        """Emit the original logging messages using the Loguru logging system."""
        try:
            record_level = logger.level(record.levelname).name
        except AttributeError:
            record_level = self.LOG_LEVEL_MAPPING.get(record.levelno, "UNKNOWN")

        depth = self.__get_logging_depth(logging.currentframe())

        log = logger.bind(request_id="app")
        log.opt(depth=depth, exception=record.exc_info).log(record_level, "[WP API] " + record.getMessage())

    @staticmethod
    def __get_logging_depth(frame: FrameType) -> int:
        """Get the logging depth of the current frame."""
        depth = 2

        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        return depth
