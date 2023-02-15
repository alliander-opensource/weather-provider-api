#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  SPDX-FileCopyrightText: 2019-2022 Alliander N.V.
#  SPDX-License-Identifier: MPL-2.0

import logging
import logging.config

import structlog

from weather_provider_api.app_config import get_setting


def add_application_metadata(logger, method_name, event_dict):
    if "app_version" not in event_dict:
        event_dict["app_version"] = get_setting("APP_VERSION")
    if "app_valid_date" not in event_dict:
        event_dict["app_valid_date"] = get_setting("APP_VALID_DATE")

    return event_dict


def initialize_logging():
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_application_metadata,
        timestamper,
        structlog.processors.UnicodeDecoder(),
    ]

    pre_chain = shared_processors

    # Setup JSON-logging to stdout
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
                    "level": get_setting("LOG_LEVEL"),
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": get_setting("LOG_LEVEL"),
                    "propagate": True,
                }
            },
        }
    )

    structlog.configure(
        processors=[structlog.stdlib.filter_by_level]
        + shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
