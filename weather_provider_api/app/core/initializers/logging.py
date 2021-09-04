#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import logging
import logging.config

import structlog

from weather_provider_api.app.core.config import Config


def initialize_logging():
    """ This function sets up the logging environment that makes sure the logs for any API component will end up as a
    part of the API.

    """
    time_stamper = structlog.processors.TimeStamper(fmt='iso')

    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_application_meta_data,
        time_stamper,
        structlog.processors.UnicodeDecoder()
    ]

    pre_chain = shared_processors

    # Setup JSON-logging to stdout
    set_json_logging_to_stdout(pre_chain)

    # Structlog
    structlog.configure(
        processors=[structlog.stdlib.filter_by_level] + shared_processors +
                   [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_application_meta_data(logger, method_name, event_dict):
    """ This function adds app data and logging information to an already existing event_dict object.

    """
    if "app_version" not in event_dict:
        event_dict["app_version"] = Config["app"]["main_version"]
    if "app_valid_date" not in event_dict:
        event_dict["app_valid_date"] = Config["app"]["valid_date"]

    event_dict["logger"] = logger
    event_dict["method_name"] = method_name

    return event_dict


def set_json_logging_to_stdout(pre_chain):
    """ This function makes sure the logger supplies JSON formatted log items.

    """
    logging.captureWarnings(True)
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(),
                    "foreign_pre_chain": pre_chain,
                }
            },
            "handlers": {
                "default": {
                    "level": Config["log_level"],
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": Config["log_level"],
                    "propagate": True,
                }
            },
        }
    )
