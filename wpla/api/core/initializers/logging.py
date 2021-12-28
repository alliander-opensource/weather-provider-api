#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0
"""
#####################
The API Logger System
#####################

This module configures and sets up the log handler for the WPLA API. The output is rendered in JSON, allowing for
specific formatting and the passing of extra information such as the API's version and expiration date in its output.
"""

import logging
import logging.config

import structlog

from wpla.configuration import Config


def add_application_metadata(logger, method_name, event_dict):
    """Adds metadata to any log event holding the WPLA API's version and expiration date.

    Args:
        logger: NOT USED. (But required by the system calling upon this function)
        method_name: NOT USED. (But required by the system calling upon this function)
        event_dict: Event dictionary to be augmented with the API version and expiration date (if not already included)

    Returns:
        An event dictionary also holding the API version and API expiration date.

    """
    if "app_version" not in event_dict:
        event_dict["app_version"] = Config['app']['version']
    if "app_valid_date" not in event_dict:
        event_dict["app_valid_date"] = Config['app']['valid_until']

    return event_dict


def initialize_logging():
    """*Logging Initializer:*

    Sets up the entire logging structure. The main output format is JSON, as it allows for easy addition of metadata
    and works well together with most logging monitors.
    """
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
