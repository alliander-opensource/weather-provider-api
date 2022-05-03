#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SPDX-FileCopyrightText: 2019-2021 Alliander N.V.
#
# SPDX-License-Identifier: MPL-2.0

"""The base configuration

Contains any settings that should be the default for the configuration.

"""

import os
import tempfile

from dateutil.parser import parse as date_parser

from wpla.__init__ import __version__

ENVIRONMENT_PREFIX = "WPLA"
CORE_API_VALIDATION_DATE = "2023-12-31"
SUPPORTED_API_VERSIONS = ["v2", "v3"]
DEFAULT_API_VERSION_VALIDATION_DATES = {"v2": "2021-12-31", "v3": "2023-12-31"}
DEFAULT_API_VERSIONS = {"v2": "3.0.0-alpha1", "v3": "3.0.0-alpha1"}


class Configuration:
    """Base settings."""
    name = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_APP_NAME", "weather_provider_lib_api"
    )
    description = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_APP_DESCRIPTION",
        "The Weather Provider Libraries and API",
    )
    version = __version__
    core_validation_date = date_parser(
        os.environ.get(
            f"{ENVIRONMENT_PREFIX}_API_VALIDATION_DATE",
            CORE_API_VALIDATION_DATE,
        )
    ).date()

    maintainer = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_APP_MAINTAINER",
        "DNB Verbindingsteam (Contact: Raoul Linnenbank)",
    )
    maintainer_email = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_MAINTAINER_EMAIL",
        "weather.provider@alliander.com",
    )

    # Supported APIs
    api_versions = {}
    for API in SUPPORTED_API_VERSIONS:
        api_versions[API] = {
            "api_validation_date": date_parser(
                os.environ.get(
                    f"{ENVIRONMENT_PREFIX}_{API.upper()}_API_VALIDATION_DATE",
                    DEFAULT_API_VERSION_VALIDATION_DATES[API],
                )
            ).date(),
            "api_version": DEFAULT_API_VERSIONS[API],
        }

    # Other configuration parameters
    show_maintainer_info = bool(
        os.environ.get(f"{ENVIRONMENT_PREFIX}_SHOW_MAINTAINER", False)
    )
    logging_level = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_DEFAULT_LOGGING_LEVEL", "INFO"
    )

    # Network settings:
    network_interface_ip = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_NETWORK_INTERFACE", "127.0.0.1"
    )
    network_interface_port = int(
        os.environ.get(f"{ENVIRONMENT_PREFIX}_NETWORK_PORT", "8080")
    )

    # Storage settings:
    repository_folder = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_REPOSITORY_FOLDER",
        os.path.join(
            tempfile.gettempdir(), f"{ENVIRONMENT_PREFIX}_repositories"
        ),
    )
    temporary_folder = os.environ.get(
        f"{ENVIRONMENT_PREFIX}_REPOSITORY_FOLDER",
        os.path.join(tempfile.gettempdir(), f"{ENVIRONMENT_PREFIX}_temp"),
    )

    debugging = False
    deployed = False
