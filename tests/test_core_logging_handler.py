# SPDX-FileCopyrightText: 2021-2026 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

# Tests for weather_provider_api.core.initializers.logging_handler.

import logging

from loguru import logger

from weather_provider_api.core.initializers.logging_handler import (
    LoggingInterceptHandler,
    initialize_logging,
)


def test_log_level_map_contains_standard_levels():
    """The intercept handler should map the standard logging levels to their loguru names."""
    level_map = LoggingInterceptHandler.log_level_map

    assert level_map[50] == "CRITICAL"
    assert level_map[40] == "ERROR"
    assert level_map[30] == "WARNING"
    assert level_map[20] == "INFO"
    assert level_map[10] == "DEBUG"
    assert level_map[0] == "NOTSET"


def test_intercept_handler_forwards_message_to_loguru():
    """Emitting a standard log record should forward the message to the loguru logger."""
    captured: list[str] = []
    sink_id = logger.add(lambda message: captured.append(message.record["message"]), level="DEBUG")

    try:
        record = logging.LogRecord(
            name="test-logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="intercepted-core-message",
            args=None,
            exc_info=None,
        )
        LoggingInterceptHandler().emit(record)
    finally:
        logger.remove(sink_id)

    assert any("intercepted-core-message" in message for message in captured)


def test_initialize_logging_reroutes_uvicorn_loggers():
    """Initializing logging should replace the handlers of existing uvicorn loggers with the intercept handler."""
    uvicorn_logger = logging.getLogger("uvicorn.test_core")
    uvicorn_logger.handlers = [logging.StreamHandler()]

    initialize_logging()

    assert len(uvicorn_logger.handlers) == 1
    assert isinstance(uvicorn_logger.handlers[0], LoggingInterceptHandler)
