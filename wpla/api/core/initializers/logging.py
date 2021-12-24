#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
import logging
import logging.config

import structlog

from wpla.configuration import Config

"""Logging system

This module sets up the logging handler for the API. Output is rendered as JSON, holding extra information such as the 
APIs version and expiration date.
"""


def add_application_metadata(logger, method_name, event_dict):
    if "app_version" not in event_dict:
        event_dict["app_version"] = Config['app']['version']
    if "app_valid_date" not in event_dict:
        event_dict["app_valid_date"] = Config['app']['valid_until']

    return event_dict


def initialize_logging():
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_application_metadata,
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.UnicodeDecoder()
    ]

    # Set up JSON logging to stdout
    logging.captureWarnings(True)
    logging.config.dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    '()': structlog.stdlib.ProcessorFormatter,
                    'processor': structlog.processors.JSONRenderer(),
                    'foreign_pre_chain': shared_processors
                }
            },
            'handlers': {
                'default': {
                    'level': Config['log_level'],
                    'class': 'logging.StreamHandler',
                    'formatter': 'json'
                }
            },
            'loggers': {
                '': {
                    'handlers': ['default'],
                    'level': Config['log_level'],
                    'propagate': True
                }
            }
        }
    )

    # noinspection PyTypeChecker
    structlog.configure(
        processors=[structlog.stdlib.filter_by_level]
                   + shared_processors
                   + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True
    )
